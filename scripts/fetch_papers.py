#!/usr/bin/env python3
"""多源论文检索器 — arXiv API结构化检索 + 中文关键词导出。"""
import urllib.request, urllib.parse, xml.etree.ElementTree as ET, json, os, sys, time
from datetime import datetime

OUTDIR = os.path.join(os.path.expanduser("~"), "codex_outputs", datetime.now().strftime("%Y-%m-%d"))
PROGRESS_FILE = os.path.join(OUTDIR, "progress.json")

CN_KEYWORDS = [
    "遥感 语义分割", "点云 语义分割 LiDAR", "LiDAR SLAM 实时",
    "视觉SLAM 多传感器融合", "三维重建 高斯泼溅", "三维重建 NeRF",
    "无人机 摄影测量 倾斜摄影", "高光谱 分类 深度学习",
    "遥感 变化检测 深度学习", "InSAR 形变监测",
    "遥感 基础模型 Transformer", "激光雷达 点云配准",
    "点云 目标检测 实例分割", "实景三维 中国", "遥感 图像超分辨率",
]

EN_QUERIES = [
    ("all:remote+sensing+AND+all:semantic+AND+all:segmentation", "RS Semantic Seg", 3),
    ("all:point+cloud+AND+all:segmentation+AND+all:LiDAR", "Point Cloud Seg", 3),
    ("all:SLAM+AND+all:visual+AND+all:real-time", "Visual SLAM", 3),
    ("all:LiDAR+AND+all:SLAM", "LiDAR SLAM", 3),
    ("all:photogrammetry+AND+all:UAV+AND+all:deep+learning", "Photogrammetry UAV", 2),
    ("all:remote+sensing+AND+all:change+AND+all:detection", "Change Detection", 3),
    ("all:3D+Gaussian+Splatting+AND+all:reconstruction", "3D Gaussian Splat", 3),
    ("all:hyperspectral+AND+all:classification+AND+all:deep+learning", "Hyperspectral", 2),
    ("all:remote+sensing+AND+all:foundation+AND+all:model", "RS Foundation Model", 3),
    ("all:remote+sensing+AND+all:object+AND+all:detection+AND+all:UAV", "RS Object Detection", 2),
    ("all:point+cloud+AND+all:registration+AND+all:deep+learning", "Point Cloud Registration", 2),
    ("all:NeRF+AND+all:3D+AND+all:reconstruction", "NeRF 3D Recon", 2),
    ("all:remote+sensing+AND+all:image+AND+all:super-resolution", "RS Super-Res", 2),
]

def load_progress() -> dict:
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"date": datetime.now().strftime("%Y-%m-%d"), "steps": {}}

def save_progress(progress: dict) -> None:
    os.makedirs(OUTDIR, exist_ok=True)
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def search_arxiv(query: str, max_results: int = 3, retries: int = 3) -> list:
    url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode({
        "search_query": query, "start": 0, "max_results": max_results,
        "sortBy": "submittedDate", "sortOrder": "descending"
    })
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "searchscinece/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                xml_data = r.read().decode("utf-8")
            ns = {"a": "http://www.w3.org/2005/Atom"}
            root = ET.fromstring(xml_data)
            papers = []
            for entry in root.findall("a:entry", ns):
                t = entry.find("a:title", ns)
                title = (t.text or "").strip().replace("\n", " ").replace("  ", " ")
                s = entry.find("a:summary", ns)
                summary = (s.text or "").strip().replace("\n", " ").replace("  ", " ")
                pub = entry.find("a:published", ns)
                published = pub.text[:10] if pub is not None and pub.text else ""
                sid = entry.find("a:id", ns)
                arxiv_id = sid.text.strip().split("/abs/")[-1] if sid is not None and sid.text else ""
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf" if arxiv_id else ""
                authors = []
                for a in entry.findall("a:author", ns):
                    n = a.find("a:name", ns)
                    if n is not None and n.text:
                        authors.append(n.text.strip())
                cats = [c.get("term","") for c in entry.findall("a:category", ns) if c.get("term")]
                papers.append({
                    "title": title, "summary": summary, "published": published,
                    "arxiv_id": arxiv_id, "pdf_url": pdf_url, "authors": authors,
                    "categories": cats, "source": "arxiv", "selected": False, "deep_analysis": {},
                })
            return papers
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 * (attempt + 1))
                continue
            print(f"  [WARN] arXiv搜索失败 [{label}]: {e}", file=sys.stderr)
            print(f"         建议: 检查网络连接，或稍后重试。关键词: {q[:60]}", file=sys.stderr)
            return []
    return []


def search_semantic_scholar(keywords_en: list, max_results: int = 5, retries: int = 3) -> list:
    """Search Semantic Scholar API for papers. No API key needed for basic access."""
    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    query = "+".join(keywords_en[:4])
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit={max_results}&fields=title,abstract,url,year,authors,externalIds,publicationVenue,openAccessPdf"
    
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "searchscinece/1.0",
                "Accept": "application/json"
            })
            with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
                data = json.loads(r.read().decode())
            
            papers = []
            for item in data.get("data", []):
                title = (item.get("title") or "").strip()
                summary = (item.get("abstract") or "")[:1000]
                year = item.get("year", "")
                published = f"{year}-01-01" if year else ""
                authors = [a.get("name", "") for a in item.get("authors", [])]
                ext_ids = item.get("externalIds", {})
                arxiv_id = ext_ids.get("ArXiv", "")
                doi = ext_ids.get("DOI", "")
                paper_id = item.get("paperId", "")
                
                # Try to get PDF URL
                pdf_url = ""
                oa = item.get("openAccessPdf")
                if oa and oa.get("url"):
                    pdf_url = oa["url"]
                elif arxiv_id:
                    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                
                # Build venue info
                venue = item.get("publicationVenue") or {}
                venue_name = venue.get("name", "") if venue else ""
                
                if title:
                    papers.append({
                        "title": title,
                        "summary": summary,
                        "published": published,
                        "arxiv_id": arxiv_id,
                        "doi": doi,
                        "paper_id": paper_id,
                        "pdf_url": pdf_url,
                        "authors": authors,
                        "venue": venue_name,
                        "source": "semantic_scholar",
                        "selected": False,
                        "deep_analysis": {},
                    })
            return papers
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 * (attempt + 1))
                continue
            print(f"  [WARN] Semantic Scholar搜索失败: {e}", file=sys.stderr)
            print(f"         建议: 检查网络连接，SS API无需密钥。关键词: {keywords[:4]}", file=sys.stderr)
            return []
    return []


def main():
    progress = load_progress()
    if progress.get("steps", {}).get("fetch") == "completed":
        existing = os.path.join(OUTDIR, "papers.json")
        if os.path.exists(existing):
            print(f"[SKIP] Already completed: {existing}")
            return existing
    os.makedirs(OUTDIR, exist_ok=True)
    all_papers, seen = [], set()

    print(f"=== SearchScience Multi-Source | {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")

    # --- arXiv ---
    print("\n--- arXiv ---")
    for q, label, n in EN_QUERIES:
        print(f"[arxiv:{label}] searching (max {n})...", end=" ")
        count_before = len(all_papers)
        for p in search_arxiv(q, n):
            if p["arxiv_id"] not in seen:
                seen.add(p["arxiv_id"])
                all_papers.append(p)
        print(f"+{len(all_papers) - count_before}")
        time.sleep(0.5)

    # --- Semantic Scholar ---
    print("\n--- Semantic Scholar ---")
    for d in EN_QUERIES[:5]:
        q, label, n = d
        print(f"[ss:{label}] searching...", end=" ")
        keywords = q.replace("all:", "").replace("+AND+", " ").split()
        count_before = len(all_papers)
        for p in search_semantic_scholar(keywords, max(n, 3)):
            key = (p.get("title", "")[:80]).lower()
            if key not in seen:
                seen.add(key)
                all_papers.append(p)
        print(f"+{len(all_papers) - count_before}")
        time.sleep(1)

    # Sort and save
    all_papers.sort(key=lambda x: x.get("published", ""), reverse=True)
    out = os.path.join(OUTDIR, "papers.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(all_papers, f, ensure_ascii=False, indent=2)

    progress.setdefault("steps", {})["fetch"] = "completed"
    progress["total_papers"] = len(all_papers)
    save_progress(progress)

    # Summary
    src_counts = {}
    for p in all_papers:
        s = p.get("source", "unknown")
        src_counts[s] = src_counts.get(s, 0) + 1
    print(f"\nTotal: {len(all_papers)} papers")
    for src, cnt in sorted(src_counts.items()):
        print(f"  {src}: {cnt}")

    for i, p in enumerate(all_papers[:20]):
        src_tag = p.get("source", "?")[:2]
        print(f"  [{i+1}] [{src_tag}] {p['published']} | {p['title'][:80]}")
    if len(all_papers) > 20:
        print(f"  ... and {len(all_papers) - 20} more")

    print(f"\nAgent should search CNKI with: {', '.join(CN_KEYWORDS[:8])}")
    return out


if __name__ == "__main__":
    main()
