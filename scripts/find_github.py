#!/usr/bin/env python3
"""
GitHub代码库搜索器 — 为论文查找对应的开源实现。
通过GitHub API搜索论文标题/方法名的代码仓库。
"""
import urllib.request, urllib.parse, json, os, sys, time
from datetime import datetime

JSON_PATH = os.path.join(os.path.expanduser("~"), "codex_outputs", datetime.now().strftime("%Y-%m-%d"), "papers.json")
GITHUB_API = "https://api.github.com/search/repositories"

def load_papers(json_path):
    if not os.path.exists(json_path):
        print(f"[错误] 论文数据文件未找到: {json_path}", file=sys.stderr)
        print(f"       请先运行: python scripts/fetch_papers.py", file=sys.stderr)
        sys.exit(1)
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_papers(json_path, papers):
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)

def search_github(query, retries=2):
    """通过GitHub API搜索代码仓库"""
    params = urllib.parse.urlencode({
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": 3
    })
    url = f"{GITHUB_API}?{params}"
    
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "searchscinece/1.0",
                "Accept": "application/vnd.github.v3+json"
            })
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read().decode())
            
            repos = []
            for item in data.get("items", [])[:3]:
                repos.append({
                    "full_name": item.get("full_name", ""),
                    "url": item.get("html_url", ""),
                    "description": (item.get("description", "") or "")[:200],
                    "stars": item.get("stargazers_count", 0),
                    "language": item.get("language", ""),
                    "updated": item.get("updated_at", ""),
                })
            return repos
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
                continue
            print(f"  [GitHub搜索失败] {e}", file=sys.stderr)
            print(f"         建议: 检查网络或GitHub API限流(60次/小时)", file=sys.stderr)
            return []
    return []

def extract_search_terms(paper):
    """从论文信息中提取搜索关键词"""
    terms = []
    title = paper.get("title", "")
    
    # 提取冒号前的缩写（如 "SAM3D: Segment Anything..." -> "SAM3D"）
    if ":" in title:
        abbrev = title.split(":")[0].strip()
        if len(abbrev) < 30 and not abbrev.startswith("http"):
            terms.append(abbrev)
    
    # 取前6个有意义的关键词
    words = [w for w in title.replace(":", "").replace(",", "").split() 
             if w.lower() not in {"a", "an", "the", "for", "and", "of", "in", "with", "to", "on", "via", "by"}]
    
    # 用前4个关键词
    if len(words) >= 4:
        terms.append(" ".join(words[:4]))
    
    return terms

def main():
    papers = load_papers(JSON_PATH)
    found_count = 0
    
    print(f"=== Search GitHub Repos ===")
    print(f"Papers: {len(papers)}")
    print()
    
    for i, p in enumerate(papers):
        # 优先选中的论文
        if not p.get("selected"):
            continue
        
        # 跳过已搜索的
        if p.get("github_url"):
            print(f"  [{i+1}] SKIP (already found): {p['github_url']}")
            continue
        
        search_terms = extract_search_terms(p)
        print(f"  [{i+1}] {p['title'][:60]}...")
        
        found = False
        for term in search_terms[:2]:  # 最多试2个搜索词
            print(f"       Searching: {term[:50]}")
            repos = search_github(term)
            
            if repos:
                best = repos[0]
                p["github_url"] = best["url"]
                p["github_info"] = {
                    "repo": best["full_name"],
                    "stars": best["stars"],
                    "language": best["language"],
                    "description": best["description"],
                    "all_candidates": repos
                }
                found_count += 1
                found = True
                print(f"       FOUND: {best['full_name']} ({best['stars']} stars)")
                break
            
            time.sleep(2)  # GitHub API rate limit
        
        if not found:
            print(f"       No repo found")
        
        # 每搜索5篇就保存一次
        if (i + 1) % 5 == 0:
            save_papers(JSON_PATH, papers)
            print(f"       [Checkpoint saved]")
        
        time.sleep(3)  # 避免触发API限流
    
    save_papers(JSON_PATH, papers)
    print(f"\n{'='*50}")
    print(f"Repos found: {found_count}")

if __name__ == "__main__":
    main()