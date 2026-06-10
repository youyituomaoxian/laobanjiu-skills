#!/usr/bin/env python3
"""
GitHub 单项目数据获取
======================
通过 OSS Insight API 获取指定项目的详细信息并输出为 JSON。

用法:
  python scripts/fetch_repo_info.py owner/repo
  python scripts/fetch_repo_info.py https://github.com/owner/repo
"""

import json
import os
import sys
import io
import re
import ssl
import urllib.request
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.upper() != "UTF-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OSS_INSIGHT_API = "https://ossinsight.io/api/mcp"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


def fetch_json(url: str, timeout: int = 15):
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": "GitHubAnalyzer/1.0"})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return json.loads(resp.read().decode())


def parse_input(text: str) -> tuple[str, str] | None:
    """从用户输入中提取 owner/repo。
    支持格式: owner/repo 或 https://github.com/owner/repo"""
    text = text.strip().rstrip("/").rstrip(".git")
    # URL 格式
    m = re.search(r"github\.com/([^/]+)/([^/\s?#]+)", text)
    if m:
        return m.group(1), m.group(2)
    # owner/repo 格式
    m = re.match(r"^([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)$", text)
    if m:
        return m.group(1), m.group(2)
    return None


def fmt_stars(n: int) -> str:
    return f"{n/1000:.1f}k" if n >= 1000 else str(n)


def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/fetch_repo_info.py owner/repo")
        print("       python scripts/fetch_repo_info.py https://github.com/owner/repo")
        sys.exit(1)

    inp = " ".join(sys.argv[1:])
    parsed = parse_input(inp)
    if not parsed:
        print(f"[!] 无法解析输入: {inp}")
        print("   期望格式: owner/repo 或 https://github.com/owner/repo")
        sys.exit(1)

    owner, repo = parsed
    print(f"[*] 正在获取 {owner}/{repo} 的数据...")

    # 获取项目详情
    url = f"{OSS_INSIGHT_API}?action=repo&owner={owner}&repo={repo}"
    data = fetch_json(url)
    if not data.get("ok") or not data.get("data"):
        print(f"[!] 获取失败: 未找到项目 {owner}/{repo}")
        sys.exit(1)

    detail = data["data"]
    stars = detail.get("stars", 0)
    forks = detail.get("forks", 0)

    # 输出数据
    result = {
        "full_name": f"{owner}/{repo}",
        "owner": {"login": owner, "avatar_url": detail.get("owner", {}).get("avatar_url", "")},
        "name": repo,
        "stars": stars,
        "stars_display": fmt_stars(stars),
        "forks": forks,
        "forks_display": fmt_stars(forks),
        "language": detail.get("language", "") or "",
        "description": detail.get("description", "") or "No description.",
    }

    # 写入 JSON
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUTPUT_DIR / f"_repo_{owner}_{repo}.json"
    out_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[+] {owner}/{repo}")
    print(f"   Star:  {result['stars_display']}")
    print(f"   Fork:  {result['forks_display']}")
    print(f"   语言:  {result['language'] or 'N/A'}")
    print(f"   描述:  {result['description'][:80]}{'...' if len(result['description']) > 80 else ''}")
    print(f"[+] 数据已保存: {out_file}")
    return out_file


if __name__ == "__main__":
    main()
