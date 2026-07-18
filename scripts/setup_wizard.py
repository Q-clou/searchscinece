#!/usr/bin/env python3
"""
SearchScience 配置向导 — 交互式创建用户研究画像。
运行: python scripts/setup_wizard.py
"""
import os, sys, json

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILES_DIR = os.path.join(SKILL_DIR, "profiles")

TEMPLATE = '''# SearchScience 用户研究画像
# 由配置向导自动生成

user:
  name: "{name}"
  institution: "{institution}"
  level: "{level}"
  language_preference: "{lang}"

research_directions:
{directions}

sources:
  cnki: {{ enabled: {cnki}, priority: 1, max_papers_per_query: 3 }}
  arxiv: {{ enabled: true, priority: 2, max_papers_per_query: 3 }}
  google_scholar: {{ enabled: true, priority: 3, max_papers_per_query: 3 }}
  pubmed: {{ enabled: {pubmed}, priority: 5, max_papers_per_query: 2 }}
  ieee: {{ enabled: false, priority: 4, max_papers_per_query: 2 }}

selection:
  max_papers_per_day: {max_daily}
  prefer_recent_days: 180
  prefer_open_access: true
  prefer_with_code: true

analysis:
  detail_level: "deep"
  language: "zh"
  include_sections: [background, method, innovation, experiments, limitations, relevance, reading_guide]

output:
  report_dir: "Desktop"
  pdf_dir: "Desktop/论文原文"
  data_dir: "~/codex_outputs"
  report_filename: "学术日报_{{date}}.pdf"
  include_english_abstract: true
  include_github_info: true
  include_key_terms: true

personal_background: |
  {background}

target_venues: []
exclude_keywords: []
'''

def ask(prompt, default=""):
    d = f" [{default}]" if default else ""
    return input(f"{prompt}{d}: ").strip() or default

def main():
    print("=" * 60)
    print("  SearchScience — 用户研究画像配置向导")
    print("=" * 60)
    print()
    print("这个向导会帮你创建个人研究画像文件。")
    print("画像会告诉 SearchScience：你的研究方向、关注的数据源、")
    print("以及你希望如何深度分析论文。")
    print()
    
    name = ask("你的名字/昵称", "Researcher")
    institution = ask("学校/机构", "")
    levels = ["本科", "硕士", "博士", "教师", "研究员", "工程师", "其他"]
    print(f"  身份: " + " | ".join(f"[{i}]{l}" for i, l in enumerate(levels)))
    level_idx = ask("选择 (数字)", "1")
    try:
        level = levels[int(level_idx)]
    except (ValueError, IndexError):
        level = "硕士"
    
    lang_choice = ask("分析语言偏好? [zh=中文为主 / en=英文为主 / bilingual=双语]", "zh")
    
    print()
    print("--- 研究方向 ---")
    print("请输入你的研究方向(一行一个，空行结束)")
    print("格式: 方向名称 | 中文关键词(逗号分隔) | 英文关键词(逗号分隔) | 权重1-10")
    print("示例: 遥感语义分割 | 遥感,语义分割 | remote sensing,semantic segmentation | 10")
    print()
    
    directions = []
    while True:
        line = input(f"  方向{directions.__len__()+1}: ").strip()
        if not line:
            break
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 3:
            directions.append({
                "name": parts[0],
                "keywords_cn": [k.strip() for k in parts[1].split(",") if k.strip()],
                "keywords_en": [k.strip() for k in parts[2].split(",") if k.strip()],
                "weight": int(parts[3]) if len(parts) >= 4 and parts[3].isdigit() else 7
            })
    
    if not directions:
        # 默认遥感方向
        directions = [{
            "name": "遥感图像处理",
            "keywords_cn": ["遥感", "深度学习", "语义分割"],
            "keywords_en": ["remote sensing", "deep learning", "semantic segmentation"],
            "weight": 10
        }]
    
    # 格式化方向
    dir_lines = []
    for d in directions:
        dir_lines.append(f'  - name: "{d["name"]}"')
        dir_lines.append(f'    keywords_cn: {json.dumps(d["keywords_cn"], ensure_ascii=False)}')
        dir_lines.append(f'    keywords_en: {json.dumps(d["keywords_en"], ensure_ascii=False)}')
        dir_lines.append(f'    weight: {d["weight"]}')
    
    print()
    cnki = ask("启用知网搜索? [y/n]", "y").lower().startswith("y")
    pubmed = ask("启用PubMed搜索? [y/n]", "n").lower().startswith("y")
    max_daily = ask("每天最多分析几篇论文?", "5")
    
    print()
    background = ask("个人研究背景简述 (可选)")
    if not background:
        background = f"{institution} {level}，研究方向为{'、'.join(d['name'] for d in directions)}。"
    
    # 生成 YAML
    yaml_content = TEMPLATE.format(
        name=name,
        institution=institution,
        level=level,
        lang=lang_choice,
        directions="\n".join(dir_lines),
        cnki="true" if cnki else "false",
        pubmed="true" if pubmed else "false",
        max_daily=max_daily,
        background=background
    )
    
    os.makedirs(PROFILES_DIR, exist_ok=True)
    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in name)
    profile_path = os.path.join(PROFILES_DIR, f"{safe_name}.yaml")
    
    # 避免覆盖
    counter = 1
    while os.path.exists(profile_path):
        profile_path = os.path.join(PROFILES_DIR, f"{safe_name}_{counter}.yaml")
        counter += 1
    
    with open(profile_path, "w", encoding="utf-8") as f:
        f.write(yaml_content)
    
    print()
    # Validate the newly created profile
    print()
    try:
        sys.path.insert(0, SKILL_DIR)
        from src.utils.config import validate_profile_data, Profile
        profile_obj = Profile(profile_path)
        is_valid, errors = validate_profile_data(profile_obj.data)
        if not is_valid:
            print("\n  [WARN] Profile has issues:")
            for e in errors:
                print(f"    - {e}")
        else:
            print("\n  [OK] Profile validation passed.")
    except Exception as e:
        print(f"\n  [NOTE] Could not validate profile: {e}")
    
    # Set up output directories
    try:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        pdf_dir = os.path.join(desktop, "论文原文")
        os.makedirs(pdf_dir, exist_ok=True)
        data_dir = os.path.expanduser("~/codex_outputs")
        os.makedirs(data_dir, exist_ok=True)
        print(f"  [OK] Output directories ready:")
        print(f"       PDF reports -> {desktop}")
        print(f"       Paper PDFs  -> {pdf_dir}")
        print(f"       Data cache  -> {data_dir}")
    except Exception as e:
        print(f"  [WARN] Could not create output dirs: {e}")
    
    print()
    print("=" * 60)
    print(f"  Profile saved: {profile_path}")
    print(f"  Run: python scripts/cli.py --profile {profile_path}")
    print(f"  Quick test: python scripts/cli.py --profile {profile_path} --status")
    print("=" * 60)
    return profile_path