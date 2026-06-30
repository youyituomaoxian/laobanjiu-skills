#!/usr/bin/env python3
"""
GitHub 热门开源项目深度分析
============================
触发命令：热门分析
分析框架：参照「软件工具学习.md」5 块结构
设计系统：Taste-Skill + UI UX PRO MAX
"""

import json
import os
import sys
import io
import urllib.request
import urllib.error
import ssl
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── Force UTF-8 stdout ──────────────────────────────────
if sys.stdout.encoding and sys.stdout.encoding.upper() != "UTF-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── Config ──────────────────────────────────────────────
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
HISTORY_FILE = OUTPUT_DIR / "analysis_history.json"
OSS_INSIGHT_API = "https://ossinsight.io/api/mcp"
MAX_REPOS = 3
FETCH_TOP_N = 10  # 多取一些用于重复过滤
PERIOD = "past_week"
LANGUAGE = "All"

# 重复项目判定阈值
STAR_GROWTH_RATE = 0.30      # Star 增长 >= 30% 视为重大更新
STAR_GROWTH_ABSOLUTE = 500   # Star 增长 >= 500 视为显著增长
HISTORY_DAYS_IGNORE = 60     # 超过 60 天的记录不再参考

# ── History Management ────────────────────────────────

def load_history() -> list:
    """加载分析历史记录。"""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []
    return []

def save_history(history: list):
    """原子保存分析历史记录（先写临时文件，再替换）。"""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    cutoff = datetime.now(timezone.utc) - timedelta(days=HISTORY_DAYS_IGNORE)
    history = [h for h in history if datetime.fromisoformat(h["date"]).replace(tzinfo=timezone.utc) > cutoff]
    tmp = HISTORY_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    os.replace(tmp, HISTORY_FILE)

def add_to_history(repos: list):
    """将本次分析的项目追加到历史记录。"""
    history = load_history()
    now = datetime.now(timezone.utc).isoformat()
    for r in repos:
        full_name = r.get("full_name", r.get("repo_name", ""))
        history.append({
            "full_name": full_name,
            "stars": r.get("stars", 0),
            "forks": r.get("forks", 0),
            "trending_score": r.get("total_score", 0),
            "date": now,
        })
    save_history(history)

def filter_duplicates(candidates: list) -> list:
    """从候选列表中过滤重复项目，返回应纳入本次分析的列表。"""
    history = load_history()
    if not history:
        return candidates[:MAX_REPOS]

    hist_index = {}
    for h in history:
        name = h["full_name"]
        if name not in hist_index or h["date"] > hist_index[name]["date"]:
            hist_index[name] = h

    selected = []
    skipped = []

    for repo in candidates:
        full_name = repo.get("repo_name", "")
        if not full_name:
            selected.append(repo)
            continue

        prev = hist_index.get(full_name)
        if prev is None:
            selected.append(repo)
            continue

        curr_stars = repo.get("stars", 0)
        prev_stars = prev.get("stars", 0)
        star_diff = curr_stars - prev_stars
        is_major_update = False

        if prev_stars > 0 and (star_diff / prev_stars) >= STAR_GROWTH_RATE:
            is_major_update = True
            print(f"    ↳ {full_name}: Star 增长 {star_diff:+,} ({star_diff/prev_stars*100:+.0f}%), 重新纳入")

        if star_diff >= STAR_GROWTH_ABSOLUTE:
            is_major_update = True

        top_scores = sorted([r.get("total_score", 0) for r in candidates], reverse=True)[:3]
        if repo.get("total_score", 0) >= (top_scores[-1] if top_scores else 0):
            is_major_update = True

        if is_major_update:
            selected.append(repo)
        else:
            skipped.append(repo)
            print(f"    ↳ {full_name}: Star 无显著变化, 跳过")

    if len(selected) < MAX_REPOS and skipped:
        need = MAX_REPOS - len(selected)
        skipped.sort(key=lambda r: r.get("total_score", 0), reverse=True)
        for r in skipped[:need]:
            print(f"    ↳ {r.get('repo_name','')}: 候选不足, 按热度补回")
            selected.append(r)

    return selected[:MAX_REPOS]

# ── API Helpers ─────────────────────────────────────────
import time
import socket

def fetch_json(url: str, timeout: int = 15, retries: int = 3):
    """带重试的 JSON API 请求。"""
    ctx = ssl.create_default_context()
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "GitHubTrendingBot/1.0"})
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                return json.loads(resp.read().decode())
        except (urllib.error.URLError, socket.timeout, OSError) as e:
            last_err = e
            if attempt < retries - 1:
                wait = 2 ** attempt
                print(f"    ⚠ 请求失败 (第{attempt+1}次), {wait}s 后重试...")
                time.sleep(wait)
    raise last_err

def get_trending(period=PERIOD, lang=LANGUAGE, top_n=FETCH_TOP_N):
    url = f"{OSS_INSIGHT_API}?action=trending&language={lang}&period={period}"
    data = fetch_json(url)
    if not data.get("ok"): raise RuntimeError(f"OSS Insight error: {data}")
    return data["data"][:top_n]

def get_repo_detail(owner: str, repo: str):
    url = f"{OSS_INSIGHT_API}?action=repo&owner={owner}&repo={repo}"
    data = fetch_json(url)
    return data.get("data") if data.get("ok") else None

def fmt_stars(n: int) -> str:
    return f"{n/1000:.1f}k" if n >= 1000 else str(n)

def avatar_color(name: str) -> str:
    h = hash(name) % 360
    return f"hsl({h}, 54%, 52%)"

def avatar_initials(name: str) -> str:
    return name[0].upper() if name else "?"

def lang_color(lang: str) -> str:
    palette = {
        "Python": "#3572A5", "TypeScript": "#3178C6", "JavaScript": "#F7DF1E",
        "Rust": "#DEA584", "Go": "#00ADD8", "Java": "#B07219",
        "C++": "#F34B7D", "C#": "#178600", "Ruby": "#701516",
        "Shell": "#89E051", "HTML": "#E34F26", "CSS": "#563D7C",
    }
    return palette.get(lang, "#6B7280")

# ── Project Analysis Data ───────────────────────────────
PROJECT_ANALYSIS = {
    "odysseus": {
        "oneliner": "跑在你自家硬件上的 ChatGPT/Claude，数据完全归你。",
        "pain": "用 ChatGPT/Claude 时总担心数据泄露？上传的代码、文档、私人邮件全都经过第三方服务器。Odysseus 给你一模一样的 AI 工作空间体验——聊天、文档、邮件、日历、深度搜索全套功能，但所有数据都留在你的机器上。",
        "scenarios": [
            "开发者想把 AI 工作流完全私有化，所有代码和文档不经过任何第三方 API",
            "团队需要一个共享的 AI 协作空间，但数据合规要求不能上公有云",
            "AI 发烧友想本地跑 LLM，搭配完整的聊天 + 搜索 + RAG + 邮件 + 日历一体化体验"
        ],
        "nosuit": "不适合只想快速用 API 调一下 LLM 的人——Odysseus 是一整套应用，不是轻量 SDK。",
        "install": "git clone https://github.com/pewdiepie-archdaemon/odysseus.git && cd odysseus && docker compose up -d --build",
        "first_run": "打开 http://localhost:7000，终端会打印初始密码，登录后去 Settings 连上你的 LLM 即可。",
        "tasks": [
            ("📝 用本地模型写一篇技术博客，全程离线", "以前：打开 ChatGPT → 粘贴 prompt → 担心数据被训练。\n\n用 Odysseus：打开 http://localhost:7000，配好本地 Ollama 端点，新建对话直接开写。全在本地。"),
            ("📧 让 AI 每天早上帮你筛邮件", "以前：每天早上打开邮箱，几百封未读，手动扫标题、删垃圾。\n\n用 Odysseus：连上 IMAP 邮箱，Agent 自动读新邮件、总结重点、按重要性排序。"),
            ("🔍 一键做深度研究，跨多个来源自动汇总", "以前：开 10 个浏览器 Tab 分别搜 Google、查文档、看论文——手动复制粘贴汇总。\n\n用 Odysseus：内置 Deep Research 功能，连接 SearXNG 搜索引擎，自动跨源搜索、抓取、汇总。")
        ],
        "alternatives": [
            ("Open WebUI", "如果你只需要一个轻量的 LLM 聊天前端，不需要邮件/日历/文档/搜索等功能"),
            ("ChatGPT/Claude 官方产品", "不在意数据隐私、不想自己运维、想要最省事"),
            ("NextChat", "更轻量的 ChatGPT 替代前端，适合单用户快速搭建")
        ],
        "golden_pair": "Odysseus + Ollama = 完全离线的 AI 工作空间。Ollama 负责本地推理，Odysseus 负责 UI 和 Agent 能力。",
        "tips": "Windows 用户推荐用 Docker Desktop 部署。如果端口 7000 被占用，在 .env 里设置 APP_PORT=7001。"
    },
    "headroom": {
        "oneliner": "在 AI Agent 读到内容之前，先帮你省 60-95% 的 token 钱。",
        "pain": "每次让 Claude/Codex 分析一段代码或日志，传过去几千上万 token，其实大部分是重复的格式、空格、注释。Headroom 在请求到达 LLM 之前就把这些东西压扁——同样的答案，几分之一的 token 开销。",
        "scenarios": [
            "重度 Claude Code / Codex 用户，月 API 账单几千刀以上，想立刻省 60%+ 的 token 开销",
            "RAG 应用开发，检索到的文档块太长、太多，塞进 context 前需要智能压缩",
            "多 Agent 协作场景，Agent 之间互相传递上下文越来越臃肿"
        ],
        "nosuit": "不适合对延迟极度敏感的场景——压缩本身有计算开销。也不适合内容极小的场景。",
        "install": "pip install \"headroom-ai[all]\"",
        "first_run": "装完后跑 headroom wrap claude，然后正常用 Claude Code。终端每次对话结束会输出 compression stats。",
        "tasks": [
            ("🔧 让 Claude Code 分析一个大型项目日志，省 80% token", "以前：把 5000 行日志直接贴给 Claude → 光传过去就花了 2 万 token。\n\n用 Headroom：headroom wrap claude 绑定一次，之后正常用。跑完几个任务后执行 headroom perf 看省了多少 token。"),
            ("📚 给 RAG 应用加一层压缩，context 省一半", "以前：检索出来的 10 篇文档全部塞进 prompt，context window 很快就满了。\n\n用 Headroom：在 Python 代码里加 from headroom import compress，检索结果压缩后再塞进 LLM。"),
            ("🔄 跨 Agent 共享压缩上下文", "以前：Agent A 处理完的结果传给 Agent B，再把全部原始内容发一遍。\n\n用 Headroom：两个 Agent 都接同一个 SharedContext，压缩后的上下文共享存储。")
        ],
        "alternatives": [
            ("RTK", "RTK 只压缩 CLI 命令的输出，覆盖面窄且不可还原"),
            ("OpenAI / Anthropic 自带的上下文管理", "只有对话历史压缩，而且绑定各自的 provider"),
            ("lean-ctx", "轻量级上下文管理器，适合单工具场景")
        ],
        "golden_pair": "Headroom + Claude Code = 省 token 省到肉痛。headroom wrap claude 一次绑定，零代码侵入。",
        "tips": "建议用 pip install 'headroom-ai[all]' 装全量版本。MCP 模式需要先 headroom mcp install 注册到 Claude Code。"
    },
    "codegraph": {
        "oneliner": "给 AI 编程助手配一份它自己能读懂的项目地图，再也不用来回翻文件。",
        "pain": "AI 编程助手每次理解你的项目都要重新读文件、找引用关系。项目一大，频繁翻文件既费 token 又容易遗漏。CodeGraph 提前把项目建好索引知识图谱。",
        "scenarios": [
            "大型 monorepo 项目，AI Agent 频繁迷失在文件间依赖关系里",
            "刚接手一个陌生产品代码库，想让 AI 快速理解整体架构",
            "CI/CD 流程里每天自动维护代码知识图谱"
        ],
        "nosuit": "不适合非常小的项目（几十个文件），手动翻一下更快。",
        "install": "npm install -g @colbymchenry/codegraph",
        "first_run": "在你项目根目录跑 codegraph init 初始化，再跑 codegraph build 建图。",
        "tasks": [
            ("🔍 让 Claude Code 理解一个大型 Go 项目的函数调用链", "以前：问 Claude → grep 搜一遍 → 逐文件读上下文 → 可能漏了间接调用。\n\n用 CodeGraph：建好图谱后照常问，直接查预索引的调用关系图。"),
            ("🔄 CI 里每天自动更新图谱，团队共享", "以前：每个开发者各自维护项目理解。\n\n用 CodeGraph：在 GitHub Actions 里加一步 codegraph build --update-only。"),
            ("🏗 接手老项目，5 分钟摸清架构", "以前：新人接手 5 年老项目，先花两周读文档。\n\n用 CodeGraph：跑 codegraph build，让 AI 基于图谱画出模块架构图。")
        ],
        "alternatives": [
            ("Claude Code 自带的文件搜索", "小项目够用。项目超过几百个文件时，CodeGraph 的预索引优势明显"),
            ("ripgrep / grep 全文搜索", "只能搜文本，搜不出调用链和类型关系"),
            ("Sourcegraph / Code Search", "功能更强但需要部署服务端。CodeGraph 是本地 CLI，零运维成本")
        ],
        "golden_pair": "CodeGraph + Claude Code 是黄金组合。build 一次图谱，后续所有 AI 编程操作都受益。",
        "tips": "CodeGraph 支持增量更新，第一次 build 后，后续 codegraph build --update-only 只扫描变化文件。"
    },
}

DEFAULT_ANALYSIS = {
    "__ai_generated": True,
    "oneliner": "（由 AI 实时分析生成）",
    "pain": "",
    "scenarios": [],
    "nosuit": "",
    "install": "",
    "first_run": "",
    "tasks": [],
    "alternatives": [],
    "golden_pair": "",
    "tips": "",
}

def match_analysis(full_name: str) -> dict:
    for key, val in PROJECT_ANALYSIS.items():
        if key in full_name.lower():
            return val
    return DEFAULT_ANALYSIS

def generate_html(repos: list, generated_at: str) -> str:
    """生成交互式深色主题 HTML 报告——Taste-Skill + UI UX PRO MAX 设计系统。"""
    raise NotImplementedError(
        "HTML template is not available in this copy. "
        "Please sync from GitHub upstream or use '模式二：单项目分析' "
        "which generates HTML via the AI agent directly."
    )

def main():
    print("[*] 正在获取 GitHub Trending 数据...")
    try:
        raw_repos = get_trending()
    except Exception as e:
        print(f"[!] 获取数据失败: {e}")
        raise
    if not raw_repos:
        print("[!] 无数据")
        sys.exit(1)
    print(f"[+] 获取到 {len(raw_repos)} 个候选项目")

    for r in raw_repos:
        full_name = r.get("repo_name", "")
        parts = full_name.split("/")
        owner, name = (parts[0], parts[1]) if len(parts) > 1 else ("", "")
        if owner and name:
            try:
                detail = get_repo_detail(owner, name)
                if detail:
                    r["stars"] = detail.get("stars", 0)
                    r["forks"] = detail.get("forks", 0)
                    r["owner"] = detail.get("owner", {})
            except Exception as e:
                print(f"[-] {full_name} 详情失败: {e}")

    print("[*] 检查历史记录，过滤重复项目...")
    selected = filter_duplicates(raw_repos)

    repos = []
    for r in selected:
        full_name = r.get("repo_name", "")
        # 复用第一次循环已获取的 detail 数据，不再重复调用 API
        repos.append(r)

    add_to_history(repos)
    print(f"\n[+] 最终入选 {len(repos)} 个项目：")
    for i, r in enumerate(repos, 1):
        fn = r.get("repo_name", "")
        print(f"  #{i} {fn}  {fmt_stars(r.get('stars',0))} stars")

    beijing = timezone(timedelta(hours=8))
    now = datetime.now(beijing)
    generated_at = now.strftime("%Y-%m-%d %H:%M CST")

    try:
        html = generate_html(repos, generated_at)
    except NotImplementedError as e:
        print(f"\n[!] HTML 模板不可用: {e}")
        print("[!] 项目数据已获取完毕，请使用模式二（单项目分析）生成报告。")
        sys.exit(1)

    if html is None:
        print("\n[!] generate_html() 返回了空内容，请检查模板。")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"github_hot_analysis_{now.strftime('%Y%m%d_%H%M')}.html"
    filepath = OUTPUT_DIR / filename
    filepath.write_text(html, encoding="utf-8")
    (OUTPUT_DIR / "latest.html").write_text(html, encoding="utf-8")
    print(f"\n[+] 报告生成: {filepath}")
    print(f"[+] 最新版: {OUTPUT_DIR / 'latest.html'}")
    return filepath

if __name__ == "__main__":
    main()
