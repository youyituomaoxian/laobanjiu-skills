#!/usr/bin/env python3
"""
热门分析素材生成 — 辅助脚本
==============================
读取最新一期热门分析数据，创建分类素材目录结构。

输出目录：
output/
├── 素材输出_YYYYMMDD_HHMM/
│   ├── 00_本期概览.md
│   ├── _projects.json          ← AI 读取用
│   ├── 【HTML报告】/
│   │   └── github_hot_analysis_YYYYMMDD_HHMM.html
│   ├── 【项目提示词】/
│   │   ├── 01_项目名_prompt.md
│   │   ├── 02_项目名_prompt.md
│   │   └── 03_项目名_prompt.md
│   └── 【口播文案】/
│       ├── 01_项目名_script.md
│       ├── 02_项目名_script.md
│       └── 03_项目名_script.md
"""

import json
import os
import sys
import io
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.upper() != "UTF-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── Config ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"

# 项目分析数据（与 github_trending_weekly.py 共享，直接引用避免重复）
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from github_trending_weekly import PROJECT_ANALYSIS, match_analysis


def find_latest_html() -> Path | None:
    """从 output/ 中找到最新带时间戳的 HTML 文件（优先 latest.html）。"""
    latest = OUTPUT_DIR / "latest.html"
    if latest.exists():
        return latest
    files = sorted(OUTPUT_DIR.glob("github_hot_analysis_*.html"), reverse=True)
    return files[0] if files else None


def parse_projects_from_html(html_path: Path) -> list[dict]:
    """从 HTML 中解析出每个项目的元数据——使用 string split 而非复杂 regex。
    支持两种格式：
    - 批量分析（多个 article.card）
    - 单项目分析（hero section 单项目）
    """
    html = html_path.read_text(encoding="utf-8")

    # 提取时间
    ts_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2} CST)', html)
    generated_at = ts_match.group(1) if ts_match else ""

    projects = []

    # 尝试模式一：批量分析（多个 article.card）
    cards = html.split('<article class="card"')
    if len(cards) > 1:
        for chunk in cards[1:]:
            proj = _parse_card_chunk(chunk)
            projects.append(proj)
        return projects, generated_at

    # 尝试模式二：单项目分析（hero section）
    proj = _parse_single_project_hero(html)
    if proj:
        projects.append(proj)

    return projects, generated_at


def _parse_card_chunk(chunk: str) -> dict:
    """从批量分析的单个卡片 chunk 解析项目数据。"""
    proj = {}

    m = re.search(r'<span class="owner">([^<]+)</span>', chunk)
    proj["owner"] = m.group(1).strip() if m else ""

    m = re.search(r'<h2 class="repo-name">\s*<a[^>]*>([^<]+)</a>', chunk)
    proj["name"] = m.group(1).strip() if m else ""

    m = re.search(r'st-stars[^>]*>.*?<span class="stat-num">([^<]+)</span>', chunk, re.DOTALL)
    proj["stars_display"] = m.group(1).strip() if m else "0"

    m = re.search(r'st-forks[^>]*>.*?<span class="stat-num">([^<]+)</span>', chunk, re.DOTALL)
    proj["forks_display"] = m.group(1).strip() if m else "0"

    m = re.search(r'lang-dot[^>]*>([^<]+)</span>', chunk)
    proj["language"] = m.group(1).strip() if m else ""

    m = re.search(r'class="card-oneliner">([^<]*)</div>', chunk)
    proj["oneliner"] = m.group(1).strip() if m else ""

    m = re.search(r'<p class="card-desc">([^<]*)</p>', chunk)
    proj["description"] = m.group(1).strip() if m else ""

    full_name = f"{proj['owner']}/{proj['name']}" if proj["owner"] and proj["name"] else ""

    def parse_num(s: str) -> int:
        s = s.lower().replace(",", "")
        if "k" in s:
            return int(float(s.replace("k", "")) * 1000)
        try:
            return int(s) if s else 0
        except ValueError:
            return 0

    return {
        "full_name": full_name,
        "owner": proj["owner"],
        "name": proj["name"],
        "stars": parse_num(proj["stars_display"]),
        "stars_display": proj["stars_display"],
        "forks": parse_num(proj["forks_display"]),
        "forks_display": proj["forks_display"],
        "language": proj["language"],
        "oneliner": proj["oneliner"],
        "description": proj["description"],
    }


def _parse_single_project_hero(html: str) -> dict | None:
    """从单项目分析的 hero section 解析项目数据。"""
    # 项目名称 (h1 in hero)
    m = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
    name = m.group(1).strip() if m else ""
    if not name:
        return None

    # 从 footer 提取 full_name (owner/repo)
    m = re.search(r'\| ([^/]+)/([^<|]+)</p>', html)
    owner = m.group(1).strip() if m else ""
    full_name = m.group(0).strip() if m else ""
    if not owner:
        owner = ""
    repo_name = name

    # Stars (第一个 data-count)
    star_match = re.search(r'data-count="(\d+)"', html)
    stars = int(star_match.group(1)) if star_match else 0

    # Forks (第二个 data-count)
    fork_match = re.search(r'data-count="(\d+)"', html[star_match.end():]) if star_match else None
    forks = int(fork_match.group(1)) if fork_match else 0

    def fmt_num(n: int) -> str:
        return f"{n/1000:.1f}k" if n >= 1000 else str(n)

    # 描述 (subtitle in hero)
    m = re.search(r'class="subtitle"[^>]*>([^<]+)</p>', html)
    description = m.group(1).strip() if m else ""

    return {
        "full_name": f"{owner}/{repo_name}",
        "owner": owner,
        "name": repo_name,
        "stars": stars,
        "stars_display": fmt_num(stars),
        "forks": forks,
        "forks_display": fmt_num(forks),
        "language": "",
        "oneliner": description[:80] + ("..." if len(description) > 80 else ""),
        "description": description,
    }


def create_material_dir(projects: list[dict], generated_at: str) -> Path:
    """创建素材输出目录结构，写入元数据 JSON。"""
    now = datetime.now(timezone(timedelta(hours=8)))
    ts = now.strftime("%Y%m%d_%H%M")
    material_dir = OUTPUT_DIR / f"素材输出_{ts}"
    material_dir.mkdir(parents=True, exist_ok=True)

    # 子目录
    html_dir = material_dir / "【HTML报告】"
    prompt_dir = material_dir / "【项目提示词】"
    script_dir = material_dir / "【口播文案】"
    cover_dir = material_dir / "【封面提示词】"
    for d in [html_dir, prompt_dir, script_dir, cover_dir]:
        d.mkdir(exist_ok=True)

    # 复制最新 HTML
    latest_html = find_latest_html()
    if latest_html:
        dest_html = html_dir / latest_html.name
        dest_html.write_text(latest_html.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"[+] HTML 已复制: {dest_html}")

    # 写入 projects_data.json（AI 用）
    data = {
        "generated_at": generated_at,
        "material_time": now.strftime("%Y-%m-%d %H:%M CST"),
        "project_count": len(projects),
        "projects": projects,
    }
    json_path = material_dir / "_projects.json"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[+] 项目数据: {json_path}")

    # 写入 00_本期概览.md（框架，内容由 AI 填充）
    overview_lines = [
        f"# 本期素材概览\n",
        f"**生成时间**: {data['material_time']}",
        f"**数据来源**: GitHub Trending (OSS Insight)",
        f"**项目数量**: {len(projects)} 个\n",
        "---\n",
        "## 素材清单\n",
    ]
    for i, p in enumerate(projects, 1):
        overview_lines.append(f"- 📊 **{p['full_name']}** 生图提示词: `【项目提示词】/{i:02d}_{p['name']}_prompt.md`")
        overview_lines.append(f"- 🎙️ **{p['full_name']}** 口播文案: `【口播文案】/{i:02d}_{p['name']}_script.md`")

    (material_dir / "00_本期概览.md").write_text(
        "\n".join(overview_lines), encoding="utf-8"
    )
    print(f"[+] 概览文件: {material_dir / '00_本期概览.md'}")

    return material_dir


def main():
    print("[*] 正在读取最新分析数据...")

    html = find_latest_html()
    if not html:
        print("[!] 未找到最新分析报告，请先执行「热门分析」")
        sys.exit(1)
    print(f"[+] 数据来源: {html}")

    projects, generated_at = parse_projects_from_html(html)
    if not projects:
        print("[!] 未能从 HTML 中解析出项目数据")
        sys.exit(1)

    print(f"[+] 解析到 {len(projects)} 个项目:")
    for i, p in enumerate(projects, 1):
        print(f"    #{i} {p['full_name']}  {p['stars_display']} stars")

    material_dir = create_material_dir(projects, generated_at)
    print(f"\n[+] 素材目录已创建: {material_dir}")
    print(f"[+] 请 AI 继续写入提示词和口播文案")

    return material_dir


if __name__ == "__main__":
    main()
