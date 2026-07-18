"""用户画像配置加载器 — 加载和验证 YAML profile 文件"""
import os
try:
    import yaml
except ImportError:
    yaml = None
from copy import deepcopy

DEFAULT_PROFILE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config")
DEFAULT_PROFILE = os.path.join(DEFAULT_PROFILE_DIR, "default_profile.yaml")

# 内置 fallback（YAML 不可用时使用）
BUILTIN_DEFAULTS = {
    "user": {"name": "User", "language_preference": "zh", "level": "研究生"},
    "research_directions": [],
    "sources": {
        "arxiv": {"enabled": True, "priority": 1, "max_papers_per_query": 3},
        "cnki": {"enabled": True, "priority": 1, "max_papers_per_query": 3},
        "google_scholar": {"enabled": True, "priority": 3, "max_papers_per_query": 3},
        "pubmed": {"enabled": False, "priority": 5, "max_papers_per_query": 2},
        "ieee": {"enabled": False, "priority": 4, "max_papers_per_query": 2},
    },
    "selection": {"max_papers_per_day": 5, "prefer_recent_days": 180, "prefer_open_access": True, "prefer_with_code": True},
    "analysis": {"detail_level": "deep", "language": "zh", "include_sections": ["background", "method", "innovation", "experiments", "limitations", "relevance"]},
    "output": {"report_dir": "Desktop", "pdf_dir": "Desktop/论文原文", "data_dir": "~/codex_outputs", "report_filename": "学术日报_{date}.pdf", "include_english_abstract": True, "include_github_info": True, "include_key_terms": True},
    "personal_background": "",
    "target_venues": [],
    "exclude_keywords": [],
    "learning_stage": {
        "stage": "beginner",
        "current_focus": "",
        "completed_topics": [],
        "next_topics": [],
        "notes": ""
    },
}
# === Profile validation ===
def validate_profile_data(data: dict):
    """校验用户画像数据结构，返回 (is_valid, errors_list)。
    每个错误都包含中文说明和修改建议。"""
    errors = []
    errors = []
    required = ["user", "research_directions", "sources"]
    for key in required:
        if key not in data:
            errors.append(f"[结构错误] 缺少必需字段 {key!r}，请在画像文件中添加此字段")
    user = data.get("user", {})
    if not isinstance(user, dict) or not user.get("name"):
        errors.append("[用户信息] user.name 字段不能为空，请设置你的姓名或昵称")
    lang = user.get("language_preference", "zh")
    if lang not in ("zh", "en", "bilingual"):
        errors.append(f"[用户信息] language_preference 值 {lang!r} 无效，可选: zh / en / bilingual")
    directions = data.get("research_directions", [])
    if not isinstance(directions, list) or len(directions) == 0:
        errors.append("[研究方向] research_directions 不能为空，至少需要一个研究方向")
    else:
        for i, d in enumerate(directions):
            if not isinstance(d, dict) or not d.get("name"):
                errors.append(f"[研究方向] 第{i+1}个方向缺少 name 字段，请填写方向名称")
            kw_cn = d.get("keywords_cn", [])
            kw_en = d.get("keywords_en", [])
            if not kw_cn and not kw_en:
                errors.append(f"[研究方向] 第{i+1}个方向缺少关键词，请至少填写 keywords_cn 或 keywords_en")
            w = d.get("weight", 5)
            if not isinstance(w, (int, float)) or w < 1 or w > 10:
                errors.append(f"[研究方向] 第{i+1}个方向的 weight 值 {w} 无效，应为 1-10 的整数")
    sources = data.get("sources", {})
    valid_src = ["arxiv", "cnki", "pubmed", "google_scholar", "ieee", "semantic_scholar"]
    enabled = 0
    for sn, cfg in sources.items():
        if sn not in valid_src:
            errors.append(f"[数据源] 未知数据源 {sn!r}，有效值: arxiv, cnki, pubmed, google_scholar, ieee, semantic_scholar")
        if cfg.get("enabled"):
            enabled += 1
    if enabled == 0:
        errors.append("[数据源] 至少需要启用一个数据源，请在 sources 中设置 enabled: true")
    sel = data.get("selection", {})
    mp = sel.get("max_papers_per_day", 5)
    if not isinstance(mp, int) or mp < 1 or mp > 20:
        errors.append(f"[筛选设置] max_papers_per_day 值 {mp} 无效，应为 1-20 的整数")
    rd = sel.get("prefer_recent_days", 180)
    if not isinstance(rd, int) or rd < 7 or rd > 730:
        errors.append(f"[筛选设置] prefer_recent_days 值 {rd} 无效，应为 7-730 的整数")
    excl = data.get("exclude_keywords", [])
    if not isinstance(excl, list):
        errors.append("[排除关键词] exclude_keywords 必须是列表格式，如 [\"medical\", \"clinical\"]")
    return len(errors) == 0, errors



class Profile:
    """用户研究画像"""
    
    def __init__(self, path: str | None = None):
        self.path = path
        self.data = deepcopy(BUILTIN_DEFAULTS)
        if path and os.path.exists(path):
            self._load(path)
        # Validate loaded config
        is_valid, errors = validate_profile_data(self.data)
        if not is_valid:
            print(f"[WARN] Profile validation warnings:")
            for e in errors:
                print(f"  - {e}")
    
    def _load(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            # 深度合并
            self._deep_merge(self.data, data)
        except ImportError:
            print("[WARN] PyYAML not installed, using built-in defaults. Run: pip install pyyaml")
        except Exception as e:
            print(f"[WARN] Failed to load profile: {e}, using defaults")
    
    def _deep_merge(self, base, override):
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    # --- 便捷属性 ---
    @property
    def user_name(self):
        return self.data.get("user", {}).get("name", "User")
    
    @property
    def language(self):
        return self.data.get("user", {}).get("language_preference", "zh")
    
    @property
    def directions(self):
        return self.data.get("research_directions", [])
    
    @property
    def enabled_sources(self):
        """返回启用的数据源，按优先级排序"""
        srcs = self.data.get("sources", {})
        enabled = [(name, cfg) for name, cfg in srcs.items() if cfg.get("enabled")]
        enabled.sort(key=lambda x: x[1].get("priority", 99))
        return enabled
    
    @property
    def max_daily_papers(self):
        return self.data.get("selection", {}).get("max_papers_per_day", 5)
    
    def get_cn_keywords(self):
        """提取所有中文关键词"""
        kws = set()
        for d in self.directions:
            for kw in d.get("keywords_cn", []):
                kws.add(kw)
        return list(kws)
    
    def get_en_keywords(self):
        """提取所有英文关键词，组合为 arXiv 查询"""
        queries = []
        for d in self.directions:
            en_kws = d.get("keywords_en", [])
            weight = d.get("weight", 5)
            name = d.get("name", "")
            if en_kws:
                query = "+AND+".join(f"all:{kw.replace(' ', '+')}" for kw in en_kws[:4])
                queries.append((query, name, min(weight // 3 + 1, 5)))
        return queries
    
    def get_output_dir(self, key="data_dir"):
        """获取输出目录，支持 ~ 展开"""
        path = self.data.get("output", {}).get(key, "~/codex_outputs")
        return os.path.expanduser(path)
    
    def get_report_path(self, date_str=None):
        """获取日报PDF完整路径"""
        from datetime import datetime
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
        report_dir = self.data.get("output", {}).get("report_dir", "Desktop")
        if report_dir == "Desktop":
            report_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        filename = self.data.get("output", {}).get("report_filename", "学术日报_{date}.pdf")
        filename = filename.replace("{date}", date_str)
        return os.path.join(report_dir, filename)


def load_profile(path=None):
    """工厂函数：加载画像"""
    if path is None:
        # 尝试找 profiles/ 目录下的文件
        profiles_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "profiles")
        if os.path.isdir(profiles_dir):
            yamls = [f for f in os.listdir(profiles_dir) if f.endswith((".yaml", ".yml"))]
            if yamls:
                path = os.path.join(profiles_dir, yamls[0])
    return Profile(path)
