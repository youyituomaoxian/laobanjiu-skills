"""Export poster HTML cards to PNG images using Playwright."""
import sys
import os
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Error: Playwright is required but not installed.")
    print("  Install with: pip install playwright && playwright install chromium")
    sys.exit(1)

def export_posters(html_path: str):
    html_path = Path(html_path).resolve()
    if not html_path.exists():
        print(f"Error: File not found: {html_path}")
        sys.exit(1)
    
    output_dir = html_path.parent
    
    with sync_playwright() as p:
        # Auto-detect installed Chromium
        pw_dir = Path.home() / "AppData" / "Local" / "ms-playwright"
        chromium_dirs = sorted(pw_dir.glob("chromium-*"), reverse=True)
        if chromium_dirs:
            exe = chromium_dirs[0] / "chrome-win64" / "chrome.exe"
            exe_path = str(exe) if exe.exists() else None
        else:
            exe_path = None
        browser = p.chromium.launch(
            executable_path=exe_path,
            headless=True
        )
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(f"file:///{html_path.as_posix()}")
        page.wait_for_timeout(2000)  # Wait for render
        
        posters = page.query_selector_all(".poster")
        print(f"Found {len(posters)} poster cards")
        
        for i, poster in enumerate(posters):
            # Get the actual element dimensions
            box = poster.bounding_box()
            if not box:
                print(f"Skipping poster {i+1}: no bounding box")
                continue
            
            # Set viewport to match poster size at 2x for retina
            page.set_viewport_size({"width": int(box["width"]), "height": int(box["height"])})
            
            # Take screenshot at 2x resolution (2160x1620)
            # Since the poster is 1080x810, 2x = 2160x1620
            png_path = output_dir / f"poster_{i+1:02d}.png"
            poster.screenshot(path=str(png_path), scale="device")
            print(f"Exported: {png_path}")
        
        browser.close()
    
    print(f"\nDone! All posters exported to: {output_dir}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python export_posters.py <cards_html_path>")
        sys.exit(1)
    export_posters(sys.argv[1])
