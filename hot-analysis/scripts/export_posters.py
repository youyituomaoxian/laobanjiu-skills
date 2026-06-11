#!/usr/bin/env python3
"""
海报卡片 → 4:3 PNG 截图
=======================
使用 Playwright 在固定 1080×810 视口渲染 HTML 并逐张截图。
输出到 HTML 同级目录的 posters/ 子目录。

用法:
  python scripts/export_posters.py
  python scripts/export_posters.py path/to/cards.html

与设备无关 — 每次渲染结果完全一致。
"""

import sys
import io
import os
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"

if sys.stdout.encoding and sys.stdout.encoding.upper() != "UTF-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CARD_W = 1080
CARD_H = 810  # 4:3
VIEWPORT_W = 1200  # 卡片固定 1080px + body padding
VIEWPORT_H = 950


def find_cards_html():
    """查找最新的海报卡片 HTML 文件"""
    candidates = list(OUTPUT_DIR.rglob("海报卡片*.html"))
    if not candidates:
        # fallback: any cards html
        candidates = list(OUTPUT_DIR.rglob("*卡片*.html"))
    if not candidates:
        candidates = list(OUTPUT_DIR.rglob("*cards*.html"))
    if not candidates:
        candidates = list(OUTPUT_DIR.rglob("compare_*卡片*.html"))
    if not candidates:
        print("[!] 未找到海报卡片 HTML 文件")
        sys.exit(1)
    return max(candidates, key=lambda p: p.stat().st_mtime)


def main():
    from playwright.sync_api import sync_playwright

    # 确定输入文件
    if len(sys.argv) > 1:
        html_path = Path(sys.argv[1]).resolve()
    else:
        html_path = find_cards_html()

    if not html_path.exists():
        print(f"[!] 文件不存在: {html_path}")
        sys.exit(1)

    print(f"[*] 源文件: {html_path}")
    print(f"[*] 视口: {VIEWPORT_W}×{VIEWPORT_H}")

    # 输出目录
    out_dir = html_path.parent / "posters"
    out_dir.mkdir(parents=True, exist_ok=True)

    file_uri = html_path.as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_page(
            viewport={"width": VIEWPORT_W, "height": VIEWPORT_H},
            device_scale_factor=2,  # 2x Retina 质量
        )
        page.goto(file_uri, wait_until="load")
        page.wait_for_timeout(2000)  # 等待字体和 CSS 完整渲染

        # 抓取所有 .poster 卡片
        posters = page.query_selector_all(".poster")
        total = len(posters)
        print(f"[*] 找到 {total} 张卡片")

        for i, poster in enumerate(posters):
            # 读取卡片内文字作为文件名提示
            try:
                title_el = poster.query_selector(".title")
                label = title_el.inner_text().strip()[:20] if title_el else ""
            except Exception:
                label = ""

            # 截图
            safe = "".join(c if c.isalnum() or c in "._- " else "_" for c in label).strip()
            fname = f"card_{i+1:02d}_{safe}.png"
            out_path = out_dir / fname
            poster.screenshot(path=str(out_path))
            print(f"  [{i+1}/{total}] {fname}")

        browser.close()

    print(f"\n[+] 完成！{total} 张 PNG 已输出到: {out_dir}")
    print(f"[+] 尺寸: {int(CARD_W*2)}×{int(CARD_H*2)}px @2x (1080×810 逻辑像素)")
    return out_dir


if __name__ == "__main__":
    main()
