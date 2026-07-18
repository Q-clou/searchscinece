"""断点续传进度管理器 — 任务中断后自动恢复"""
import json, os
from datetime import datetime


# === Robustness utilities (retry, safe I/O, logging) ===
import logging, functools

_LOGGER = None

def get_logger():
    global _LOGGER
    if _LOGGER is None:
        _LOGGER = logging.getLogger("searchscinece")
        _LOGGER.setLevel(logging.INFO)
        if not _LOGGER.handlers:
            _LOGGER.addHandler(logging.StreamHandler())
    return _LOGGER

def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*a, **kw):
            logger = get_logger()
            last_exc = None
            for attempt in range(max_attempts):
                try:
                    return func(*a, **kw)
                except Exception as e:
                    last_exc = e
                    if attempt < max_attempts - 1:
                        import time
                        wait = delay * (backoff ** attempt)
                        logger.warning(f"Retry {attempt+2}/{max_attempts} for {func.__name__}: {e}")
                        time.sleep(wait)
            raise last_exc
        return wrapper
    return decorator

def safe_write_json(filepath: str, data, indent: int = 2) -> bool:
    import os as _os
    _os.makedirs(_os.path.dirname(filepath) or ".", exist_ok=True)
    tmp = filepath + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        _os.replace(tmp, filepath)
        return True
    except Exception as e:
        get_logger().error(f"Failed write {filepath}: {e}")
        if _os.path.exists(tmp):
            try: _os.remove(tmp)
            except: pass
        return False

def safe_text(val, max_len: int = 3000) -> str:
    if val is None: return ""
    if isinstance(val, str): return val.strip()[:max_len]
    if isinstance(val, (int, float, bool)): return str(val)
    return str(val)[:max_len]




# === Simple TTL Cache for API responses ===
class APICache:
    """Simple file-backed TTL cache for API responses with automatic expiry."""
    """Simple file-backed TTL cache for API responses."""
    
    def __init__(self, cache_dir: str, ttl_seconds: int = 3600):
        import os as _os
        self.cache_dir = _os.path.expanduser(cache_dir)
        self.ttl = ttl_seconds
        self._cache = {}
        self._load()
    
    def _path(self):
        import os as _os
        _os.makedirs(self.cache_dir, exist_ok=True)
        return _os.path.join(self.cache_dir, "api_cache.json")
    
    def _load(self):
        import json as _json, os as _os, time as _time
        path = self._path()
        if _os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = _json.load(f)
                now = _time.time()
                # Filter expired
                self._cache = {
                    k: v for k, v in data.items()
                    if v.get("expires", 0) > now
                }
            except Exception:
                self._cache = {}
    
    def _save(self):
        import json as _json
        try:
            with open(self._path(), "w", encoding="utf-8") as f:
                _json.dump(self._cache, f, ensure_ascii=False)
        except Exception:
            pass
    
    def get(self, key: str, default=None):
        import time as _time
        entry = self._cache.get(key)
        if entry and entry.get("expires", 0) > _time.time():
            return entry["value"]
        if entry:
            del self._cache[key]
        return default
    
    def set(self, key: str, value, ttl: int | None = None) -> None:
        import time as _time
        t = ttl if ttl is not None else self.ttl
        self._cache[key] = {
            "value": value,
            "expires": _time.time() + t,
            "cached_at": _time.time()
        }
        # Auto-save every 10 sets
        if len(self._cache) % 10 == 0:
            self._save()
    
    def clear(self) -> None:
        self._cache = {}
        self._save()
    
    def stats(self) -> dict:
        import time as _time
        now = _time.time()
        total = len(self._cache)
        expired = sum(1 for v in self._cache.values() if v.get("expires", 0) <= now)
        return {"total": total, "expired": expired, "valid": total - expired}

# === Paper deduplication ===
def dedup_papers(papers: list, threshold: float = 0.80) -> tuple:
    """Fuzzy deduplicate papers by title similarity + arXiv ID matching.
    Keeps the version with more metadata (longer abstract, more authors).
    Returns (deduplicated_list, removed_count).
    """
    import re
    from difflib import SequenceMatcher

    def normalize(title):
        t = title.lower()
        t = re.sub(r'[^a-z0-9\u4e00-\u9fff\s]', '', t)
        t = re.sub(r'\s+', ' ', t).strip()
        return t

    def is_similar(t1, t2):
        if not t1 or not t2:
            return False
        n1, n2 = normalize(t1), normalize(t2)
        if n1 == n2:
            return True
        if len(n1) < 10 or len(n2) < 10:
            return False
        # Substring check: one title contained within another
        if n1 in n2 or n2 in n1:
            return True
        return SequenceMatcher(None, n1, n2).ratio() >= threshold

    def paper_score(p):
        score = 0
        score += min(len(p.get("summary", "")), 200)
        score += len(p.get("authors", [])) * 10
        if p.get("doi"):
            score += 30
        if p.get("venue"):
            score += 20
        if p.get("arxiv_id"):
            score += 20
        return score

    kept = []
    removed = 0

    # First pass: arXiv ID exact match
    seen_arxiv = {}
    for p in papers:
        aid = p.get("arxiv_id", "")
        if aid and aid in seen_arxiv:
            existing = seen_arxiv[aid]
            if paper_score(p) > paper_score(existing):
                kept.remove(existing)
                kept.append(p)
                seen_arxiv[aid] = p
            removed += 1
        elif aid:
            seen_arxiv[aid] = p
            kept.append(p)
        else:
            kept.append(p)

    # Second pass: fuzzy title match
    result = []
    for p in kept:
        is_dup = False
        for r in result:
            if is_similar(p.get("title", ""), r.get("title", "")):
                if paper_score(p) > paper_score(r):
                    result.remove(r)
                    result.append(p)
                is_dup = True
                removed += 1
                break
        if not is_dup:
            result.append(p)

    return result, removed

class ProgressTracker:
    """追踪多步骤任务的进度，支持中断恢复"""
    
    def __init__(self, data_dir: str, date_str: str | None = None):
        self.data_dir = os.path.expanduser(data_dir)
        self.date_str = date_str or datetime.now().strftime("%Y-%m-%d")
        self.work_dir = os.path.join(self.data_dir, self.date_str)
        self.progress_file = os.path.join(self.work_dir, "progress.json")
        self._data = None
    
    def _ensure_dir(self):
        os.makedirs(self.work_dir, exist_ok=True)
    
    @property
    def data(self):
        if self._data is None:
            self._data = self._load()
        return self._data
    
    def _load(self):
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {"date": self.date_str, "steps": {}, "stats": {}}
    
    def save(self):
        self._ensure_dir()
        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def is_completed(self, step_name: str) -> bool:
        return self.data.get("steps", {}).get(step_name) == "completed"
    
    def mark_completed(self, step_name: str, **stats) -> None:
        self.data.setdefault("steps", {})[step_name] = "completed"
        for k, v in stats.items():
            self.data.setdefault("stats", {})[k] = v
        self.data["last_updated"] = datetime.now().isoformat()
        self.save()
    
    def mark_in_progress(self, step_name: str, **meta) -> None:
        info = {"status": "in_progress", "started": datetime.now().isoformat()}
        info.update(meta)
        self.data.setdefault("steps", {})[step_name] = info
        self.save()
    
    def mark_failed(self, step_name: str, error_msg: str) -> None:
        self.data.setdefault("steps", {})[step_name] = {
            "status": "failed",
            "error": str(error_msg),
            "timestamp": datetime.now().isoformat()
        }
        self.save()
    
    def get_pending_steps(self, all_steps: list) -> list:
        """返回尚未完成的步骤列表"""
        return [s for s in all_steps if not self.is_completed(s)]
    
    def get_papers_file(self) -> str:
        return os.path.join(self.work_dir, "papers.json")
    
    def reset_step(self, step_name: str) -> None:
        """重置某个步骤（允许重新执行）"""
        if step_name in self.data.get("steps", {}):
            del self.data["steps"][step_name]
        self.save()
    
    def reset_all(self) -> None:
        self._data = {"date": self.date_str, "steps": {}, "stats": {}}
        self.save()
    
    def summary(self) -> str:
        """返回人类可读的进度摘要"""
        steps = self.data.get("steps", {})
        lines = [f"进度报告 — {self.date_str}"]
        for name, state in steps.items():
            if isinstance(state, dict):
                status = state.get("status", "unknown")
                lines.append(f"  [{status.upper():12s}] {name}")
            elif state == "completed":
                lines.append(f"  [COMPLETED   ] {name}")
            else:
                lines.append(f"  [{state.upper():12s}] {name}")
        return "\n".join(lines)
