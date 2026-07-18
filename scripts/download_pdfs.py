#!/usr/bin/env python3
"""
论文PDF下载器 — 从arXiv/开放获取链接下载论文原文PDF。
支持断点续传，已下载的不重复下载。
"""
import urllib.request, json, os, sys, time, ssl
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

OUTDIR = os.path.join(os.path.expanduser("~"), "Desktop", "论文原文", datetime.now().strftime("%Y-%m-%d"))
JSON_PATH = os.path.join(os.path.expanduser("~"), "codex_outputs", datetime.now().strftime("%Y-%m-%d"), "papers.json")

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


def download_single_paper(paper, outdir, idx, total):
    """Download a single paper PDF. Returns (paper, status, size_kb)."""
    arxiv_id = paper.get("arxiv_id", "")
    pdf_url = paper.get("pdf_url", "")
    
    if not pdf_url or not arxiv_id:
        return paper, "no_url", 0
    
    filename = f"{arxiv_id}.pdf"
    save_path = os.path.join(outdir, filename)
    
    if os.path.exists(save_path):
        paper["local_pdf"] = save_path
        return paper, "exists", os.path.getsize(save_path) // 1024
    
    ok, size = download_pdf(pdf_url, save_path)
    if ok:
        paper["local_pdf"] = save_path
        return paper, "ok", size // 1024
    else:
        return paper, "failed", 0

def download_pdf(url, save_path, retries=3):
    """带重试的PDF下载"""
    for attempt in range(retries):
        try:
            # 允许自签名证书
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            req = urllib.request.Request(url, headers={
                "User-Agent": "searchscinece/1.0 (contact: research@example.com)"
            })
            with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
                data = r.read()
            
            # 验证是否真的是PDF
            if data[:4] == b'%PDF':
                with open(save_path, "wb") as f:
                    f.write(data)
                return True, len(data)
            else:
                # 可能是HTML重定向页
                if attempt < retries - 1:
                    time.sleep(2)
                    continue
                return False, 0
        except Exception as e:
            if attempt < retries - 1:
                print(f"  Retry {attempt+2}/{retries} after error: {e}")
                time.sleep(3 * (attempt + 1))
                continue
            print(f"  [下载失败] {e}", file=sys.stderr)
            print(f"         建议: 检查网络连接，确认该论文可开放获取", file=sys.stderr)
            return False, 0
    return False, 0

def main():
    papers = load_papers(JSON_PATH)
    os.makedirs(OUTDIR, exist_ok=True)
    
    downloaded = 0
    skipped = 0
    failed = 0
    
    print(f"=== Download PDFs ===")
    print(f"Target: {OUTDIR}")
    print(f"Papers: {len(papers)}")
    print()
    
    for i, p in enumerate(papers):
        # 优先选中的论文
        if not p.get("selected"):
            continue
        
        arxiv_id = p.get("arxiv_id", "")
        pdf_url = p.get("pdf_url", "")
        
        if not pdf_url or not arxiv_id:
            continue
        
        filename = f"{arxiv_id}.pdf"
        save_path = os.path.join(OUTDIR, filename)
        
        if os.path.exists(save_path):
            p["local_pdf"] = save_path
            skipped += 1
            print(f"  [{i+1}] SKIP (exists): {p['title'][:60]}")
            continue
        
        print(f"  [{i+1}] DOWNLOAD: {p['title'][:60]}...")
        ok, size = download_pdf(pdf_url, save_path)
        
        if ok:
            p["local_pdf"] = save_path
            downloaded += 1
            print(f"         OK: {size//1024} KB -> {filename}")
        else:
            failed += 1
            print(f"         FAILED")
        
        time.sleep(1)  # 礼貌延迟
    
    # 保存更新后的papers.json
    save_papers(JSON_PATH, papers)
    
    print(f"\n{'='*50}")
    print(f"Downloaded: {downloaded} | Skipped: {skipped} | Failed: {failed}")
    print(f"PDFs at: {OUTDIR}")

if __name__ == "__main__":
    main()