#!/usr/bin/env python3
"""Export poster HTML cards to PNG images using Playwright.

hot-compare 专用版本。与 hot-analysis 版的差异：
  - 输出到 <html 所在目录>/posters/ 子目录（hot-compare SKILL.md 规定）
  - 显式 device_scale_factor=2，保证 1080×810 逻辑画布出图 2160×1620

用法:
  python scripts/export_posters.py output/compare_xxx_卡片_YYYYMMDD_HHMM.html
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Error: Playwright is required but not installed.")
    print("  Install with: pip install playwright && playwright install chromium")
    sys.exit(1)

# 1080×810 逻辑画布 → 2160×1620 出图
DEVICE_SCALE = 2


def export_posters(html_path: str) -> Path:
    html_path = Path(html_path).resolve()
    if not html_path.exists():
        print(f"Error: File not found: {html_path}")
        sys.exit(1)

    output_dir = html_path.parent / "posters"
    output_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        # 自动探测已安装的 Chromium
        exe_path = None
        pw_dir = Path.home() / "AppData" / "Local" / "ms-playwright"
        chromium_dirs = sorted(pw_dir.glob("chromium-*"), reverse=True)
        if chromium_dirs:
            exe = chromium_dirs[0] / "chrome-win64" / "chrome.exe"
            if exe.exists():
                exe_path = str(exe)

        browser = p.chromium.launch(executable_path=exe_path, headless=True)
        page = browser.new_page(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=DEVICE_SCALE,
        )
        page.goto(f"file:///{html_path.as_posix()}")
        page.wait_for_timeout(2000)  # 等字体与渐变渲染完成

        posters = page.query_selector_all(".poster")
        print(f"Found {len(posters)} poster cards")

        if not posters:
            print('[!] 未找到 .poster 元素——卡片 HTML 里每张卡必须带 class="poster"')
            browser.close()
            return output_dir

        for i, poster in enumerate(posters):
            box = poster.bounding_box()
            if not box:
                print(f"Skipping poster {i+1}: no bounding box")
                continue

            # 视口对齐卡片尺寸；device_scale_factor 已在建页时锁定为 2
            page.set_viewport_size(
                {"width": int(box["width"]), "height": int(box["height"])}
            )

            png_path = output_dir / f"poster_{i + 1:02d}.png"
            poster.screenshot(path=str(png_path), scale="device")
            print(f"Exported: {png_path}  ({int(box['width']) * DEVICE_SCALE}x"
                  f"{int(box['height']) * DEVICE_SCALE}px)")

        browser.close()

    print(f"\nDone! {len(posters)} posters exported to: {output_dir}")
    return output_dir


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/export_posters.py <cards_html_path>")
        sys.exit(1)
    export_posters(sys.argv[1])
