#!/usr/bin/env python3
"""
SearchScience CLI — 统一命令行入口。
用法:
  python scripts/cli.py --profile profiles/qian6.yaml          # 完整流程
  python scripts/cli.py --profile profiles/qian6.yaml --step fetch  # 仅抓取
  python scripts/cli.py --profile profiles/qian6.yaml --step analyze # 仅分析
  python scripts/cli.py --profile profiles/qian6.yaml --step report  # 仅生成报告
  python scripts/cli.py --profile profiles/qian6.yaml --resume       # 断点续传
  python scripts/setup_wizard.py                                     # 配置向导
"""
import os, sys, argparse, json
from datetime import datetime

# 将 src 目录加入 path
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SKILL_DIR)

# 延迟导入，避免依赖缺失时无法显示帮助
def get_imports():
    from src.utils.config import load_profile
    from src.utils.progress import ProgressTracker, safe_write_json
    return load_profile, ProgressTracker, safe_write_json

STEPS = ["fetch", "select", "analyze", "download", "github", "report"]

# CLI display helpers
class Spinner:
    _chars = ['|', '/', '-', '\\']

    def __init__(self, message='Working'):
        self.message = message
        self._idx = 0
        self._active = False

    def start(self):
        self._active = True
        import sys
        sys.stdout.write('\r  ' + self.message + ' ... ')
        sys.stdout.flush()

    def tick(self):
        if not self._active:
            return
        import sys
        c = self._chars[self._idx % 4]
        self._idx += 1
        sys.stdout.write('\r  ' + self.message + ' ' + c + ' ')
        sys.stdout.flush()

    def done(self, result=''):
        import sys
        self._active = False
        status = ' ' + result if result else ' Done'
        sys.stdout.write('\r  ' + self.message + status + '     \n')
        sys.stdout.flush()


def print_header(title):
    width = 50
    print()
    print('=' * width)
    print('  ' + title)
    print('=' * width)


def print_step(step_num, total, name):
    print('\n[' + str(step_num) + '/' + str(total) + '] ' + name + '...')


def print_ok(msg=''):
    print('  [OK] ' + msg)


def print_warn(msg=''):
    print('  [WARN] ' + msg)


def print_err(msg=''):
    print('  [ERROR] ' + msg)



# CLI display helpers
class Spinner:
    _chars = ['|', '/', '-', '\\']

    def __init__(self, message='Working'):
        self.message = message
        self._idx = 0
        self._active = False

    def start(self):
        self._active = True
        import sys
        sys.stdout.write('\r  ' + self.message + ' ... ')
        sys.stdout.flush()

    def tick(self):
        if not self._active:
            return
        import sys
        c = self._chars[self._idx % 4]
        self._idx += 1
        sys.stdout.write('\r  ' + self.message + ' ' + c + ' ')
        sys.stdout.flush()

    def done(self, result=''):
        import sys
        self._active = False
        status = ' ' + result if result else ' Done'
        sys.stdout.write('\r  ' + self.message + status + '     \n')
        sys.stdout.flush()


def print_header(title):
    width = 50
    print()
    print('=' * width)
    print('  ' + title)
    print('=' * width)


def print_step(step_num, total, name):
    print('\n[' + str(step_num) + '/' + str(total) + '] ' + name + '...')


def print_ok(msg=''):
    print('  [OK] ' + msg)


def print_warn(msg=''):
    print('  [WARN] ' + msg)


def print_err(msg=''):
    print('  [ERROR] ' + msg)


# === CLI display helpers ===
class Spinner:
    _chars = [chr(124), chr(47), chr(45), chr(92)]

    def __init__(self, message="Working"):
        self.message = message
        self._idx = 0
        self._active = False

    def start(self):
        self._active = True
        import sys
        sys.stdout.write("\r  " + self.message + " ... ")
        sys.stdout.flush()

    def tick(self):
        if not self._active:
            return
        import sys
        c = self._chars[self._idx % 4]
        self._idx += 1
        sys.stdout.write("\r  " + self.message + " " + c + " ")
        sys.stdout.flush()

    def done(self, result=""):
        import sys
        self._active = False
        status = " " + result if result else " Done"
        sys.stdout.write("\r  " + self.message + status + "     \n")
        sys.stdout.flush()


def print_header(title):
    width = 50
    print()
    print("=" * width)
    print("  " + title)
    print("=" * width)


def print_step(step_num, total, name):
    print("\n[" + str(step_num) + "/" + str(total) + "] " + name + "...")


def print_ok(msg=""):
    print("  [OK] " + msg)


def print_warn(msg=""):
    print("  [WARN] " + msg)


def print_err(msg=""):
    print("  [ERROR] " + msg)


def cmd_fetch(profile, tracker, safe_write_json_func=None):
    """Step 1: 多源论文抓取"""
    if tracker.is_completed("fetch"):
        papers_file = tracker.get_papers_file()
        if os.path.exists(papers_file):
            print(f"[SKIP] Fetch already completed. Papers at: {papers_file}")
            return papers_file
    
    tracker.mark_in_progress("fetch", sources=[s[0] for s in profile.enabled_sources])
    
    from datetime import datetime
    import urllib.request, urllib.parse, xml.etree.ElementTree as ET, time
    
    outdir = os.path.join(profile.get_output_dir(), tracker.date_str)
    os.makedirs(outdir, exist_ok=True)
    
    all_papers = []
    seen_ids = set()
    
    # arXiv 抓取
    en_queries = profile.get_en_keywords()
    for query_str, label, max_n in en_queries:
        print(f"[arxiv:{label}] searching (max {max_n})...")
        try:
            url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode({
                "search_query": query_str, "start": 0, "max_results": max_n,
                "sortBy": "submittedDate", "sortOrder": "descending"
            })
            req = urllib.request.Request(url, headers={"User-Agent": "searchscinece/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                xml_data = r.read().decode("utf-8")
            
            ns = {"a": "http://www.w3.org/2005/Atom"}
            root = ET.fromstring(xml_data)
            for entry in root.findall("a:entry", ns):
                t = entry.find("a:title", ns)
                title = (t.text or "").strip().replace("\n", " ").replace("  ", " ")
                s = entry.find("a:summary", ns)
                summary = (s.text or "").strip().replace("\n", " ").replace("  ", " ")
                pub = entry.find("a:published", ns)
                published = pub.text[:10] if pub is not None and pub.text else ""
                sid = entry.find("a:id", ns)
                arxiv_id = sid.text.strip().split("/abs/")[-1] if sid is not None and sid.text else ""
                
                if arxiv_id and arxiv_id not in seen_ids:
                    seen_ids.add(arxiv_id)
                    authors = []
                    for a in entry.findall("a:author", ns):
                        n = a.find("a:name", ns)
                        if n is not None and n.text:
                            authors.append(n.text.strip())
                    all_papers.append({
                        "title": title, "summary": summary, "published": published,
                        "arxiv_id": arxiv_id, "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}.pdf",
                        "authors": authors, "source": "arxiv", "selected": False,
                        "deep_analysis": {},
                    })
            print(f"  -> {len(all_papers)} total")
        except Exception as e:
            print(f"  [WARN] arXiv search failed for '{label}': {e}")
        time.sleep(0.5)
    
    all_papers.sort(key=lambda x: x.get("published", ""), reverse=True)
    
    papers_file = tracker.get_papers_file()
    if safe_write_json_func:
        safe_write_json_func(papers_file, all_papers)
    else:
        with open(papers_file, "w", encoding="utf-8") as f:
            json.dump(all_papers, f, ensure_ascii=False, indent=2)
    
    tracker.mark_completed("fetch", total_papers=len(all_papers), sources_used=["arxiv"] + 
                           ([s[0] for s in profile.enabled_sources if s[0] != "arxiv"]))
    
    print(f"\n  Papers saved: {papers_file} ({len(all_papers)} papers)")
    print(f"  NOTE: CNKI/PubMed/Scholar sources require web_search via agent.")
    print(f"  CN Keywords for agent: {', '.join(profile.get_cn_keywords()[:10])}")
    return papers_file


def cmd_report(profile, tracker):
    """Step 6: 生成PDF日报"""
    papers_file = tracker.get_papers_file()
    if not os.path.exists(papers_file):
        print(f"Error: {papers_file} not found. Run fetch first.", file=sys.stderr)
        sys.exit(1)
    
    # 调用 generate_report.py
    report_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generate_report.py")
    import subprocess
    result = subprocess.run([sys.executable, report_script, papers_file, "--profile", profile.path or ""],
                          capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)
    
    tracker.mark_completed("report")


def cmd_status(profile, tracker):
    """查看当前进度"""
    print_header("CURRENT STATUS")
    print(tracker.summary())


def cmd_reset(tracker, step=None):
    """重置进度"""
    if step:
        tracker.reset_step(step)
        print(f"  Reset step: {step}")
    else:
        confirm = input("Reset ALL progress? [y/N]: ")
        if confirm.lower() == "y":
            tracker.reset_all()
            print("  All progress reset.")


def main():
    parser = argparse.ArgumentParser(
        description="SearchScience — 多源学术论文深度分析系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 完整流程：抓取 -> 筛选 -> 分析 -> 下载 -> 搜索代码 -> 生成日报
  python cli.py --profile profiles/qian6.yaml

  # 分步执行（适合调试）
  python cli.py --profile profiles/qian6.yaml --step fetch    # 仅抓取论文
  python cli.py --profile profiles/qian6.yaml --step report   # 仅生成PDF日报

  # 中断后继续
  python cli.py --profile profiles/qian6.yaml --resume        # 从上次中断处继续

  # 进度管理
  python cli.py --profile profiles/qian6.yaml --status        # 查看当前进度
  python cli.py --profile profiles/qian6.yaml --reset fetch   # 重置抓取步骤
  python cli.py --profile profiles/qian6.yaml --reset         # 全部重置

  # 首次使用：创建个人画像
  python setup_wizard.py

Note:
  筛选(select)和深度分析(analyze)步骤需要 Codex Agent 执行。
  仅运行脚本时，这两个步骤会跳过，由 Agent 补充。
        """
    )
    parser.add_argument("--profile", "-p", help="用户画像 YAML 文件路径")
    parser.add_argument("--step", choices=STEPS, help="仅执行指定步骤")
    parser.add_argument("--resume", action="store_true", help="从中断处继续执行")
    parser.add_argument("--status", action="store_true", help="显示当前进度")
    parser.add_argument("--reset", nargs="?", const="__all__", help="重置进度 (可指定步骤名)")
    
    args = parser.parse_args()
    
    load_profile, ProgressTracker, safe_write_json = get_imports()
    profile = load_profile(args.profile)
    tracker = ProgressTracker(profile.get_output_dir())
    
    if args.status:
        cmd_status(profile, tracker)
        return
    
    if args.reset:
        step = None if args.reset == "__all__" else args.reset
        cmd_reset(tracker, step)
        return
    
    if args.resume:
        pending = tracker.get_pending_steps(STEPS)
        print(f"  Resuming from: {pending[0] if pending else 'all done'}")
        # fall through to execute
    
    if args.step:
        steps_to_run = [args.step]
    else:
        steps_to_run = [s for s in STEPS if not tracker.is_completed(s)]
        if not steps_to_run:
            print("All steps completed! Use --reset to start over.")
            return
    
    for step in steps_to_run:
        print(f"\n{'='*50}")
        print(f"  STEP: {step}")
        print(f"{'='*50}")
        
        if step == "fetch":
            cmd_fetch(profile, tracker, safe_write_json)
        elif step == "select":
            print("  Selection is done by the AI agent during deep analysis.")
            print("  Run with the Codex agent for automatic selection + analysis.")
            tracker.mark_completed("select")
        elif step == "analyze":
            print("  Deep analysis is done by the AI agent.")
            print("  Run with the Codex agent for automatic analysis.")
        elif step == "download":
            script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "download_pdfs.py")
            import subprocess
            subprocess.run([sys.executable, script], check=False)
        elif step == "github":
            script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "find_github.py")
            import subprocess
            subprocess.run([sys.executable, script], check=False)
        elif step == "report":
            cmd_report(profile, tracker)
    
    print(f"\n{'='*50}")
    print("  Done!")
    print(f"{'='*50}")
    tracker.summary()

if __name__ == "__main__":
    main()
