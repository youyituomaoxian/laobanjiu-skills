#!/usr/bin/env python3
"""hot-compare 素材生成 — 辅助脚本
====================================
汇总一次对比分析的全部产出，创建分类素材目录结构，供 AI 写入提示词与口播稿。

产出目录：
output/
└── 素材输出_YYYYMMDD_HHMM/
    ├── 00_本期概览.md
    ├── _projects.json            ← AI 读取用（对比项目元数据）
    ├── 【HTML报告】/              ← 长页 HTML + 卡片 HTML
    ├── 【海报PNG】/               ← posters/poster_NN.png
    ├── 【封面提示词】/
    ├── 【项目提示词】/
    └── 【口播文案】/

用法:
  python scripts/generate_material.py
  python scripts/generate_material.py owner1/repo1 owner2/repo2 owner3/repo3

不传参数时，自动读取 output/_repo_*.json（由 fetch_repo_info.py 写出，24 小时内）。
"""

from __future__ import annotations

import io
import json
import re
import sys
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.upper() != "UTF-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── Config ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
STALE_HOURS = 24  # _repo_*.json 的保鲜期

SUBDIRS = ["【HTML报告】", "【海报PNG】", "【封面提示词】", "【项目提示词】", "【口播文案】"]


# ── 对比项目收集 ──

def parse_repo_arg(text: str) -> str | None:
    """从 owner/repo 或 GitHub URL 提取 owner/repo。"""
    text = text.strip().rstrip("/").rstrip(".git")
    m = re.search(r"github\.com/([^/]+)/([^/\s?#]+)", text)
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    m = re.match(r"^([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)$", text)
    return f"{m.group(1)}/{m.group(2)}" if m else None


def collect_projects(argv: list[str]) -> list[dict]:
    """收集对比项目。

    优先用命令行传入的 owner/repo（权威）；否则回退到 output/_repo_*.json。
    """
    explicit = [p for p in (parse_repo_arg(a) for a in argv) if p]

    cache: dict[str, dict] = {}
    for f in OUTPUT_DIR.glob("_repo_*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        full = d.get("full_name")
        if full:
            d["_mtime"] = f.stat().st_mtime
            cache[full] = d

    if explicit:
        projects = []
        for full in explicit:
            hit = cache.get(full)
            if hit:
                hit.pop("_mtime", None)
                projects.append(hit)
            else:
                owner, name = full.split("/", 1)
                projects.append({
                    "full_name": full, "owner": owner, "name": name,
                    "stars": 0, "stars_display": "N/A", "forks": 0,
                    "forks_display": "N/A", "language": "",
                    "description": "（未取到元数据，请先运行 fetch_repo_info.py）",
                })
        return projects

    cutoff = datetime.now().timestamp() - STALE_HOURS * 3600
    fresh = [d for d in cache.values() if d.get("_mtime", 0) >= cutoff]
    fresh.sort(key=lambda d: d.get("_mtime", 0), reverse=True)
    for d in fresh:
        d.pop("_mtime", None)
    return fresh


# ── 产出物定位 ──

def _newest(pattern: str, exclude: str | None = None) -> Path | None:
    files = sorted(OUTPUT_DIR.glob(pattern), reverse=True)
    if exclude:
        files = [f for f in files if exclude not in f.name]
    return files[0] if files else None


def find_long_page() -> Path | None:
    return _newest("compare_*.html", exclude="_卡片_")


def find_cards_html() -> Path | None:
    return _newest("compare_*_卡片_*.html")


def find_posters() -> list[Path]:
    return sorted((OUTPUT_DIR / "posters").glob("poster_*.png"))


# ── 主流程 ──

def create_material_dir(projects: list[dict]) -> Path:
    now = datetime.now(timezone(timedelta(hours=8)))
    ts = now.strftime("%Y%m%d_%H%M")
    material_dir = OUTPUT_DIR / f"素材输出_{ts}"

    dirs = {name: material_dir / name for name in SUBDIRS}
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []

    long_page = find_long_page()
    if long_page:
        shutil.copy2(long_page, dirs["【HTML报告】"] / long_page.name)
        copied.append(f"长页 HTML → 【HTML报告】/{long_page.name}")
    else:
        print("[!] 未找到长页对比报告（output/compare_*.html）")

    cards_html = find_cards_html()
    if cards_html:
        shutil.copy2(cards_html, dirs["【HTML报告】"] / cards_html.name)
        copied.append(f"卡片 HTML → 【HTML报告】/{cards_html.name}")
    else:
        print("[!] 未找到卡片 HTML（output/compare_*_卡片_*.html）")

    posters = find_posters()
    for png in posters:
        shutil.copy2(png, dirs["【海报PNG】"] / png.name)
    if posters:
        copied.append(f"{len(posters)} 张海报 PNG → 【海报PNG】/")
    else:
        print("[!] 未找到海报 PNG（output/posters/）——请先跑 export_posters.py")

    for line in copied:
        print(f"[+] {line}")

    overview = [
        "# 本期对比素材概览\n",
        f"**生成时间**: {now.strftime('%Y-%m-%d %H:%M CST')}",
        f"**数据来源**: OSS Insight API + GitHub README",
        f"**对比对象**: {len(projects)} 个\n",
        "---\n",
        "## 对比对象\n",
    ]
    for i, p in enumerate(projects, 1):
        overview.append(f"{i}. **{p['full_name']}** — {p.get('stars_display', 'N/A')} stars"
                        f"{' · ' + p['language'] if p.get('language') else ''}")
    overview += [
        "\n---\n",
        "## 素材清单\n",
        f"- 📝 综合封面提示词: `【封面提示词】/00_封面_prompt.md`",
    ]
    for i, p in enumerate(projects, 1):
        overview.append(f"- 📊 **{p['full_name']}** 生图提示词: `【项目提示词】/{i:02d}_{p['name']}_prompt.md`")
    overview += [
        f"- 🎙️ 完整口播稿: `【口播文案】/00_完整口播稿_script.md`",
        f"\n> 口播稿按海报卡片编号分段：卡1 封面总览 → 卡2+ 各项目身份卡 → 矩阵对决 → 组合串联 → 高手路径\n",
    ]

    (material_dir / "00_本期概览.md").write_text("\n".join(overview), encoding="utf-8")

    data = {
        "material_time": now.strftime("%Y-%m-%d %H:%M CST"),
        "project_count": len(projects),
        "projects": projects,
        "poster_count": len(posters),
        "long_page": long_page.name if long_page else None,
        "cards_html": cards_html.name if cards_html else None,
    }
    json_path = material_dir / "_projects.json"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[+] 项目数据: {json_path}")
    print(f"[+] 概览文件: {material_dir / '00_本期概览.md'}")
    return material_dir


def main() -> Path:
    print("[*] 正在汇总对比分析产出...")

    projects = collect_projects(sys.argv[1:])
    if not projects:
        print("[!] 未识别到对比项目。")
        print("    解决：先对每个项目运行 python scripts/fetch_repo_info.py owner/repo，")
        print("    或直接传入：python scripts/generate_material.py owner1/repo1 owner2/repo2")
    else:
        print(f"[+] 对比对象 {len(projects)} 个:")
        for i, p in enumerate(projects, 1):
            print(f"    #{i} {p['full_name']}  {p.get('stars_display', 'N/A')} stars")

    material_dir = create_material_dir(projects)
    print(f"\n[+] 素材目录已创建: {material_dir}")
    print("[+] 请 AI 继续写入封面提示词、各项目提示词与完整口播稿")
    return material_dir


if __name__ == "__main__":
    main()
