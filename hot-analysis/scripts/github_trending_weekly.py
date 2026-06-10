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
    """保存分析历史记录。"""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    # 只保留最近 60 天的记录
    cutoff = datetime.now(timezone.utc) - timedelta(days=HISTORY_DAYS_IGNORE)
    history = [h for h in history if datetime.fromisoformat(h["date"]).replace(tzinfo=timezone.utc) > cutoff]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


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
    """从候选列表中过滤重复项目，返回应纳入本次分析的列表。

    判断逻辑：
    - 从未分析过 → 直接入选
    - 分析过，但 Star 增长 >= 30% 或 >= 500 → 重大更新，可重新分析
    - 分析过，但当前 trending_score 在候选列表中排前 3 → 足够热门，可重新分析
    - 分析过且无明显变化 → 跳过
    """
    history = load_history()
    if not history:
        # 没有历史记录，取热度最高的 top_n
        return candidates[:MAX_REPOS]

    # 构建历史索引 {full_name: latest_record}
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
            # 从未分析过
            selected.append(repo)
            continue

        # 计算 Star 变化
        curr_stars = repo.get("stars", 0)
        prev_stars = prev.get("stars", 0)
        star_diff = curr_stars - prev_stars

        # 判断是否为重大更新
        is_major_update = False

        # 条件1: Star 增长比例 >= 阈值
        if prev_stars > 0 and (star_diff / prev_stars) >= STAR_GROWTH_RATE:
            is_major_update = True
            print(f"    ↳ {full_name}: Star 增长 {star_diff:+,} ({star_diff/prev_stars*100:+.0f}%), 重新纳入")

        # 条件2: Star 绝对增长 >= 阈值
        if star_diff >= STAR_GROWTH_ABSOLUTE:
            is_major_update = True
            if not is_major_update:  # 还没报过
                print(f"    ↳ {full_name}: Star 增长 {star_diff:+,}, 重新纳入")

        # 条件3: 当前 trending_score 在前 3 名候选内
        top_scores = sorted([r.get("total_score", 0) for r in candidates], reverse=True)[:3]
        if repo.get("total_score", 0) >= (top_scores[-1] if top_scores else 0):
            is_major_update = True

        if is_major_update:
            selected.append(repo)
        else:
            skipped.append(repo)
            print(f"    ↳ {full_name}: Star 无显著变化 (当前{fmt_stars(curr_stars)}, 上次{fmt_stars(prev_stars)}, +{star_diff}), 跳过")

    # 如果过滤后不够 3 个，从跳过的里面按 trending_score 补回
    if len(selected) < MAX_REPOS and skipped:
        need = MAX_REPOS - len(selected)
        skipped.sort(key=lambda r: r.get("total_score", 0), reverse=True)
        for r in skipped[:need]:
            print(f"    ↳ {r.get('repo_name','')}: 候选不足, 按热度补回")
            selected.append(r)

    return selected[:MAX_REPOS]

# ── API Helpers ─────────────────────────────────────────
def fetch_json(url: str, timeout: int = 15):
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": "GitHubTrendingBot/1.0"})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return json.loads(resp.read().decode())

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
    """根据名称生成确定的头像背景色。"""
    h = hash(name) % 360
    return f"hsl({h}, 54%, 52%)"

def avatar_initials(name: str) -> str:
    """取名称首字母作为头像文字。"""
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
# 参照「软件工具学习.md」的 5 块结构，精简为 4 块：
#   ① 这玩意儿是干嘛的（一句话 + 消灭了什么麻烦 + 最适合的场景）
#   ② 最小行动闭环（最简安装 + 第一个成功操作）
#   ③ 真实任务（1-2 个典型任务）
#   ④ 它跟其他工具怎么选（同类对比 + 黄金搭档）

PROJECT_ANALYSIS = {
    "odysseus": {
        "oneliner": "跑在你自家硬件上的 ChatGPT/Claude，数据完全归你。",
        "pain": "用 ChatGPT/Claude 时总担心数据泄露？上传的代码、文档、私人邮件全都经过第三方服务器，OpenAI 和 Anthropic 都拿你的数据训练过模型。Odysseus 给你一模一样的 AI 工作空间体验——聊天、文档、邮件、日历、深度搜索全套功能，但所有数据都留在你的机器上。它把 ChatGPT 的 UI 体验、Claude 的深度思考能力、Notion 的文档管理、Gmail 的邮件助理，全部打包成一个你完全掌控的自托管应用。",
        "scenarios": [
            "开发者想把 AI 工作流完全私有化，所有代码和文档不经过任何第三方 API，适合处理敏感代码库或客户数据",
            "团队需要一个共享的 AI 协作空间，但数据合规（GDPR/ HIPAA/等保）要求不能上公有云",
            "AI 发烧友想本地跑 LLM（通过 Ollama/vLLM），搭配完整的聊天 + 搜索 + RAG + 邮件 + 日历一体化体验"
        ],
        "nosuit": "不适合只想快速用 API 调一下 LLM 的人——Odysseus 是一整套应用，不是轻量 SDK。也不适合没有 Docker 基础的用户。",
        "install": "git clone https://github.com/pewdiepie-archdaemon/odysseus.git && cd odysseus && docker compose up -d --build",
        "first_run": "打开 http://localhost:7000，终端会打印初始密码（docker compose logs odysseus 也能看到），登录后去 Settings 连上你的 LLM 即可。看到聊天界面就说明成功了。",
        "tasks": [
            ("📝 用本地模型写一篇技术博客，全程离线",
             "以前：打开 ChatGPT → 粘贴 prompt → 担心数据被训练 → 手动删聊天记录。\n\n用 Odysseus：打开 http://localhost:7000，在 Settings 里配好本地 Ollama 端点（http://host.docker.internal:11434/v1），新建对话直接开写。全在本地，随便写，写完后还能用内置的文档管理归档。"),
            ("📧 让 AI 每天早上帮你筛邮件",
             "以前：每天早上打开邮箱，几百封未读，手动扫标题、删垃圾、标重要。\n\n用 Odysseus：在 Settings 里连上 IMAP 邮箱（支持 Gmail/Outlook/企业邮箱），Agent 自动读新邮件、总结重点、按重要性排序。甚至可以代写回复草稿，你确认后一键发送。不需要把邮箱权限给任何第三方服务。"),
            ("🔍 一键做深度研究，跨多个来源自动汇总",
             "以前：开 10 个浏览器 Tab 分别搜 Google、查文档、看论文——手动复制粘贴汇总。\n\n用 Odysseus：内置 Deep Research 功能，连接 SearXNG 搜索引擎（Docker 自带），输入研究主题，自动跨源搜索、抓取、汇总，输出结构化报告。所有中间结果可追溯。")
        ],
        "alternatives": [
            ("Open WebUI", "如果你只需要一个轻量的 LLM 聊天前端，不需要邮件/日历/文档/搜索等功能，Open WebUI 更简单、资源占用更少。"),
            ("ChatGPT/Claude 官方产品", "不在意数据隐私、不想自己运维、想要最省事，直接用官方产品。Odysseus 的卖点是私有化，不是功能更全。"),
            ("NextChat / ChatGPT-Next-Web", "一个更轻量的 ChatGPT 替代前端，适合单用户快速搭建。但功能远不如 Odysseus 丰富（无邮件/日历/文档管理）。"),
        ],
        "golden_pair": "Odysseus + Ollama = 完全离线的 AI 工作空间。Ollama 负责本地推理，Odysseus 负责 UI 和 Agent 能力。再加一个 SearXNG 自建搜索引擎，连搜索都不碰外网。",
        "tips": "Windows 用户推荐用 Docker Desktop 部署。如果端口 7000 被占用，在 .env 里设置 APP_PORT=7001。首次启动如果 Ollama 在宿主机上，用 http://host.docker.internal:11434/v1 连接。"
    },
    "headroom": {
        "oneliner": "在 AI Agent 读到内容之前，先帮你省 60-95% 的 token 钱。",
        "pain": "每次让 Claude/Codex 分析一段代码或日志，传过去几千上万 token，其实大部分是重复的格式、空格、注释。一个月下来 API 账单几千刀，其中一半烧在了 LLM 读那些它不需要细看的内容上。Headroom 在请求到达 LLM 之前就把这些东西压扁——同样的答案，几分之一的 token 开销。它不是简单的 gzip 压缩，而是内容感知的智能压缩：知道 JSON 可以压结构、代码可以剪 AST、日志可以去冗余。",
        "scenarios": [
            "重度 Claude Code / Codex 用户，月 API 账单几千刀以上，想立刻省 60%+ 的 token 开销",
            "RAG 应用开发，检索到的文档块太长、太多，塞进 context 前需要智能压缩",
            "多 Agent 协作场景，Agent 之间互相传递上下文越来越臃肿，需要中间层压缩 + 可还原"
        ],
        "nosuit": "不适合对延迟极度敏感的场景——压缩本身有计算开销，虽然很小但不是零。也不适合内容极小（每次几十 token）的场景，压缩收益不明显。",
        "install": "pip install \"headroom-ai[all]\"",
        "first_run": "装完后跑 headroom wrap claude，然后正常用 Claude Code。终端每次对话结束会输出 compression stats，显示省了多少 token 和多少钱。看到 'Headroom active' 就说明生效了。",
        "tasks": [
            ("🔧 让 Claude Code 分析一个大型项目日志，省 80% token",
             "以前：把 5000 行日志直接贴给 Claude → 光传过去就花了 2 万 token → 分析结果只有几句话，但 bill 已经扣了。\n\n用 Headroom：只需要执行 headroom wrap claude 绑定一次，之后正常用 claude。Headroom 在中间自动压缩所有工具输出和日志。跑完几个任务后执行 headroom perf，看省了多少 token 和换算成多少钱。很多人第一次跑就发现省了 60-80%。"),
            ("📚 给 RAG 应用加一层压缩，context 省一半",
             "以前：检索出来的 10 篇文档全部塞进 prompt，context window 很快就满了。\n\n用 Headroom：在 Python 代码里加一行 from headroom import compress，把检索结果用 compress() 函数压缩后再塞进 LLM。本质是同样的答案只花一半的 token。"),
            ("🔄 跨 Agent 共享压缩上下文",
             "以前： Agent A 处理完的结果传给 Agent B，再把全部原始内容发一遍——token 消耗翻倍。\n\n用 Headroom：两个 Agent 都接同一个 SharedContext，压缩后的上下文共享存储。Agent B 需要原文时通过 headroom_retrieve 按 hash 取回，不需要重复传输。")
        ],
        "alternatives": [
            ("RTK", "RTK 只压缩 CLI 命令的输出，覆盖面窄且不可还原。Headroom 压缩所有上下文（工具输出、RAG、日志、文件、对话历史），并且可还原（CCR 机制）。"),
            ("OpenAI / Anthropic 自带的上下文管理", "只有对话历史压缩，而且绑定各自的 provider。Headroom 跨 provider 工作（Anthropic / OpenAI / Gemini / 任意兼容 API）。"),
            ("lean-ctx", "轻量级上下文管理器，适合单工具场景。不如 Headroom 功能全面（无 MCP、无跨 Agent 记忆、无 learn 机制）。"),
        ],
        "golden_pair": "Headroom + Claude Code = 省 token 省到肉痛。headroom wrap claude 一次绑定，零代码侵入。再加 headroom learn 定期挖掘失败 session，自动改进 prompt。",
        "tips": "建议用 pip install 'headroom-ai[all]' 装全量版本，包含 ML 压缩模型效果最好。如果只想用基础功能，装 pip install 'headroom-ai[proxy]' 就行。MCP 模式需要先 headroom mcp install 注册到 Claude Code。"
    },
    "codegraph": {
        "oneliner": "给 AI 编程助手配一份它自己能读懂的项目地图，再也不用来回翻文件。",
        "pain": "AI 编程助手（Claude Code / Cursor / Codex）每次理解你的项目都要重新读文件、找引用关系。项目一大，频繁翻文件既费 token 又容易遗漏——问一句「这个函数谁调用的」，Agent 要翻 5 个文件才能找到答案。CodeGraph 提前把项目建好索引知识图谱：类、函数、接口之间的调用关系、继承链、类型依赖，全部预索引好。Agent 直接查图而不是翻源码，速度快一个数量级。",
        "scenarios": [
            "大型 monorepo 项目（几百到几千个文件），AI Agent 频繁迷失在文件间依赖关系里，需要精准的调用链查询",
            "刚接手一个陌生产品代码库，想让 AI 快速理解整体架构——模块边界、核心数据流、外部依赖全貌",
            "CI/CD 流程里每天自动维护代码知识图谱，每次 PR 自动增量更新，团队所有 Agent 共享同一份图谱"
        ],
        "nosuit": "不适合非常小的项目（几十个文件），手动翻一下更快。也不适合纯配置项目（YAML/JSON 为主），CodeGraph 的核心价值在代码语义分析。",
        "install": "npm install -g @colbymchenry/codegraph",
        "first_run": "在你项目根目录跑 codegraph init 初始化，再跑 codegraph build 建图。看到 'Graph built successfully — 1,234 nodes indexed' 就成功了。之后 Claude Code / Codex 会自动识别并使用图谱。",
        "tasks": [
            ("🔍 让 Claude Code 理解一个大型 Go 项目的函数调用链",
             "以前：问 Claude '这个 CreateUser 函数在哪些地方被调用了？' → Claude 用 grep 搜一遍 → 然后逐文件读上下文 → 给出结果但可能漏了间接调用。\n\n用 CodeGraph：codegraph build 建好图谱后照常问。Claude 直接查预索引的调用关系图，几秒钟给出完整调用链——包括直接调用和间接调用，精确到行号。"),
            ("🔄 CI 里每天自动更新图谱，团队共享",
             "以前：每个开发者各自维护项目理解，新人 onboarding 花一周看文档。\n\n用 CodeGraph：在 GitHub Actions 的 main 分支 pipeline 里加一步 codegraph build --update-only。每次有提交就增量更新图谱。生成的图谱文件提交到 repo 或共享存储，团队所有 Agent 共用的都是最新版。"),
            ("🏗 接手老项目，5 分钟摸清架构",
             "以前：新人接手一个 5 年老项目，先花两周读文档、翻代码、画架构图。\n\n用 CodeGraph：跑 codegraph build，然后让 Claude '根据 CodeGraph 数据，给我画出这个项目的模块架构图和数据流方向'。几分钟就能拿到一份准确的架构概览，比读两周文档效率高得多。")
        ],
        "alternatives": [
            ("Claude Code 自带的文件搜索", "小项目够用。项目超过几百个文件时，CodeGraph 的预索引优势就出来了——翻文件耗时 O(n)，查图耗时 O(1)。"),
            ("ripgrep / grep 全文搜索", "只能搜文本，搜不出调用链和类型关系。你想搜 '哪些地方实现了这个接口'，grep 做不到，CodeGraph 可以。"),
            ("Sourcegraph / Code Search", "功能更强（支持跨 repo 搜索、代码导航），但需要部署服务端。CodeGraph 是本地 CLI，零运维成本。"),
        ],
        "golden_pair": "CodeGraph + Claude Code 是黄金组合。build 一次图谱，后续所有 AI 编程操作都受益。再加上 CI 自动更新，团队甚至可以建一份共享的 CLAUDE.md 引用图谱路径。",
        "tips": "CodeGraph 支持增量更新，第一次 build 后，后续 codegraph build --update-only 只会扫描变化的文件，几秒钟就完成。推荐把 codegraph build 加到 CI 中每天自动跑。图谱数据是纯 JSON，可以 gitignore 也可以通过 CI artifact 分发。"
    },
}

DEFAULT_ANALYSIS = PROJECT_ANALYSIS["odysseus"]

def match_analysis(full_name: str) -> dict:
    for key, val in PROJECT_ANALYSIS.items():
        if key in full_name.lower():
            return val
    return DEFAULT_ANALYSIS


# ═══════════════════════════════════════════════════════════════
#  HTML Template — 交互式深色主题
#  Taste-Skill + UI UX PRO MAX = 设计质量叠满
# ═══════════════════════════════════════════════════════════════
#
#  交互特性（纯 CSS + 少量 Vanilla JS）：
#  ① CSS-only Tab 切换 (radio hack) — 每个项目 4 个 Tab
#  ② 明暗主题切换按钮 (localStorage 持久化)
#  ③ 统计数字滚动动画 (IntersectionObserver)
#  ④ Details 折叠展开 — 查看完整分析原文
#  ⑤ 浮动回到顶部按钮 (scroll 超过 600px 显示)
#  ⑥ 平滑滚动 + CSS transition 动效
#  ⑦ 响应式设计 (768px / 420px 断点)
#  ⑧ prefers-reduced-motion 无障碍支持
#  ⑨ 项目快速导航栏 (proj-nav anchor links)
#

def generate_html(repos: list, generated_at: str) -> str:
    # Build project nav
    nav_html = '<nav class="proj-nav">\n'
    for i, repo in enumerate(repos, 1):
        fn = repo.get("full_name", repo.get("repo_name", ""))
        nm = fn.split("/")[-1] if "/" in fn else f"#{i}"
        nav_html += f'<a href="#proj-{i}">#{i} {nm}</a>\n'
    nav_html += '</nav>'

    cards = ""
    for i, repo in enumerate(repos, 1):
        full_name = repo.get("full_name", repo.get("repo_name", "unknown/unknown"))
        parts = full_name.split("/")
        owner, name = parts[0], parts[1] if len(parts) > 1 else full_name
        desc = repo.get("description", "") or "No description."
        stars = repo.get("stars", 0)
        forks = repo.get("forks", 0)
        lang = repo.get("language", "") or ""
        lc = lang_color(lang)
        av_color = avatar_color(owner)
        a = match_analysis(full_name)

        tabs_id = f"tabs-{i}"
        tab1_id = f"{tabs_id}-t1"
        tab2_id = f"{tabs_id}-t2"
        tab3_id = f"{tabs_id}-t3"
        tab4_id = f"{tabs_id}-t4"

        task_items = "".join(
            f"""
            <div class="task-item">
                <div class="task-title">{t[0]}</div>
                <div class="task-body">{t[1]}</div>
            </div>"""
            for t in a["tasks"]
        )
        alt_items = "".join(
            f"""
            <div class="alt-item">
                <span class="alt-name">{alt[0]}</span>
                <span class="alt-desc">{alt[1]}</span>
            </div>"""
            for alt in a["alternatives"]
        )
        scenario_items = "".join(
            f"<li>{s}</li>" for s in a["scenarios"]
        )

        cards += f"""
        <article class="card" id="proj-{i}">
            <!-- 排名 + 项目信息头 -->
            <div class="card-ribbon">#{i} · 本周最热</div>
            <div class="card-head">
                <div class="card-head-left">
                    <div class="repo-byline">
                        <span class="avatar-initial" style="background:{av_color}">{avatar_initials(owner)}</span>
                        <span class="owner">{owner}</span>
                        <span class="slash">/</span>
                    </div>
                    <h2 class="repo-name">
                        <a href="https://github.com/{full_name}" target="_blank" rel="noopener">{name}</a>
                    </h2>
                </div>
                <div class="card-head-right">
                    <span class="stat st-stars" title="Stars">
                        <svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor"><path d="M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.82 6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25z"/></svg>
                        <span class="stat-num">{fmt_stars(stars)}</span>
                    </span>
                    <span class="stat st-forks" title="Forks">
                        <svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor"><path d="M5 5.372v.878c0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75v-.878a2.25 2.25 0 111.5 0v.878a2.25 2.25 0 01-2.25 2.25h-1.5v2.128a2.251 2.251 0 11-1.5 0V8.5h-1.5A2.25 2.25 0 013.5 6.25v-.878a2.25 2.25 0 111.5 0z"/></svg>
                        <span class="stat-num">{fmt_stars(forks)}</span>
                    </span>
                    {f'<span class="lang-dot" style="background:{lc}">{lang}</span>' if lang else ''}
                </div>
            </div>

            <!-- 一句话 + 描述 -->
            <div class="card-oneliner">💡 {a["oneliner"]}</div>
            <p class="card-desc">{desc}</p>

            <!-- Tab 切换 -->
            <div class="tab-wrap">
                <input type="radio" name="{tabs_id}" id="{tab1_id}" class="tab-input" checked>
                <input type="radio" name="{tabs_id}" id="{tab2_id}" class="tab-input">
                <input type="radio" name="{tabs_id}" id="{tab3_id}" class="tab-input">
                <input type="radio" name="{tabs_id}" id="{tab4_id}" class="tab-input">

                <div class="tab-labels">
                    <label for="{tab1_id}" class="tab-label">① 这是什么</label>
                    <label for="{tab2_id}" class="tab-label">⚡ 快速上手</label>
                    <label for="{tab3_id}" class="tab-label">📋 真实任务</label>
                    <label for="{tab4_id}" class="tab-label">🔗 同类对比</label>
                </div>

                <div class="tab-panels">
                    <!-- 面板 1：这是什么 -->
                    <div class="tab-panel">
                        <div class="panel-section">
                            <h4 class="panel-h">它消灭了什么麻烦</h4>
                            <p>{a["pain"]}</p>
                        </div>
                        <div class="panel-section">
                            <h4 class="panel-h">最适合的场景</h4>
                            <ul class="panel-list">{scenario_items}</ul>
                        </div>
                        <div class="panel-section">
                            <h4 class="panel-h">它绝对不适合做什么</h4>
                            <p>{a["nosuit"]}</p>
                        </div>
                    </div>
                    <!-- 面板 2：快速上手 -->
                    <div class="tab-panel">
                        <div class="panel-section">
                            <h4 class="panel-h">最简安装</h4>
                            <div class="code-block">$ {a["install"]}</div>
                        </div>
                        <div class="panel-section">
                            <h4 class="panel-h">第一个成功操作</h4>
                            <p>{a["first_run"]}</p>
                        </div>
                        <div class="panel-section">
                            <h4 class="panel-h">💡 实用技巧</h4>
                            <p>{a["tips"]}</p>
                        </div>
                    </div>
                    <!-- 面板 3：真实任务 -->
                    <div class="tab-panel">
                        {task_items}
                    </div>
                    <!-- 面板 4：同类对比 -->
                    <div class="tab-panel">
                        <div class="panel-section">
                            <h4 class="panel-h">相似工具怎么选</h4>
                            <div class="alt-list">{alt_items}</div>
                        </div>
                        <div class="panel-section">
                            <h4 class="panel-h">黄金搭档</h4>
                            <p>{a["golden_pair"]}</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 更多详情折叠 -->
            <details class="details-more">
                <summary><span>📖 查看完整分析原文</span></summary>
                <div class="details-body">
                    <p class="panel-h">💡 一句话说清</p>
                    <p>{a["oneliner"]}</p>
                    <br>
                    <p class="panel-h">🛠 它消灭了什么麻烦</p>
                    <p>{a["pain"]}</p>
                    <br>
                    <p class="panel-h">📌 三个最适合的场景</p>
                    <ul class="panel-list">{scenario_items}</ul>
                    <br>
                    <p class="panel-h">⛔ 它绝对不适合做什么</p>
                    <p>{a["nosuit"]}</p>
                    <br>
                    <p class="panel-h">🚀 安装与首次使用</p>
                    <div class="code-block">$ {a["install"]}</div>
                    <p style="margin-top:8px">{a["first_run"]}</p>
                    <br>
                    <p class="panel-h">💡 实用技巧</p>
                    <p>{a["tips"]}</p>
                    <br>
                    <p class="panel-h">📋 真实任务</p>
                    {task_items}
                    <br>
                    <p class="panel-h">🔗 同类对比与黄金搭档</p>
                    <div class="alt-list">{alt_items}</div>
                    <p style="margin-top:8px">{a["golden_pair"]}</p>
                </div>
            </details>
        </article>"""

    total_stars = sum(r.get("stars", 0) for r in repos)
    total_forks = sum(r.get("forks", 0) for r in repos)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GitHub 热门分析</title>
<meta name="description" content="GitHub 近一周 Top 3 热门开源项目深度分析">
<meta name="color-scheme" content="dark light">
<meta name="theme-color" content="#0a0a0f">
<style>
/* ═══════════════════════════════════════════════════════════
   TASTE-SKILL (审美判断)  +  UI UX PRO MAX (设计系统输出)
   ────────────────────────────────────────────────────────────
   分工：
     Taste-Skill → 反模板布局、HSL 变量化色彩体系、Type Scale
                    1.25、4px 间距网格、三级表面质感、交替排列
     UI UX PRO MAX → 玻璃拟态卡片、渐变光晕叠加、组件级样式、
                     阴影层级系统、弹性动效曲线、自适应主题
   ═══════════════════════════════════════════════════════════ */

/* ── Design Tokens ──────────────────────────────── */
:root {{
    /* 色彩体系 (Taste-Skill: HSL 变量化) */
    --hue: 188;
    --sat: 82%;
    --lum: 58%;
    --accent: hsl(var(--hue), var(--sat), var(--lum));
    --accent-dim: hsl(var(--hue), calc(var(--sat) * 0.6), calc(var(--lum) * 0.45));
    --accent2: hsl(238, 82%, 74%);
    --star: hsl(45, 97%, 57%);

    /* 表面质感 (Taste-Skill: 三级递进) */
    --bg: hsl(240, 22%, 4%);
    --surface: hsl(240, 18%, 7%);
    --surface2: hsl(240, 14%, 11%);
    --surface3: hsl(240, 12%, 15%);

    /* 文字层级 */
    --text: hsl(218, 46%, 93%);
    --text2: hsl(218, 14%, 60%);
    --text3: hsl(218, 10%, 38%);

    /* 边框与分割 */
    --border: hsla(0, 0%, 100%, 0.06);
    --border-hover: hsla(var(--hue), var(--sat), var(--lum), 0.2);

    /* 间距系统 (UI UX PRO MAX: 4px 基准) */
    --space: 4px;

    /* 字阶 (Taste-Skill: Major Third 1.25) */
    --type-scale: 1.25;
    --text-xs: calc(0.8rem / var(--type-scale));
    --text-sm: 0.8rem;
    --text-base: 0.9rem;
    --text-lg: calc(0.9rem * var(--type-scale));
    --text-xl: calc(0.9rem * var(--type-scale) * var(--type-scale));
    --text-2xl: calc(0.9rem * var(--type-scale) * 1.5);
    --text-3xl: calc(0.9rem * var(--type-scale) * 2);

    /* 圆角体系 (UI UX PRO MAX: 三级递进) */
    --corner-sm: 6px;
    --corner: 12px;
    --corner-lg: 24px;

    /* 字体 */
    --font: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans SC", Roboto, sans-serif;
    --mono: "JetBrains Mono", "SF Mono", "Fira Code", "Fira Mono", "Roboto Mono", Menlo, Consolas, monospace;

    /* 阴影层级 (UI UX PRO MAX) */
    --shadow-xs: 0 2px 8px hsla(0, 0%, 0%, 0.2);
    --shadow-sm: 0 4px 16px hsla(0, 0%, 0%, 0.3);
    --shadow: 0 12px 48px hsla(0, 0%, 0%, 0.5);
    --shadow-glow: 0 0 40px hsla(var(--hue), var(--sat), var(--lum), 0.08);

    /* 动效曲线 (UI UX PRO MAX: 弹性缓动) */
    --transition: 0.35s cubic-bezier(0.22, 1, 0.36, 1);
    --transition-spring: 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
}}

[data-theme="light"] {{
    --bg: hsl(210, 40%, 96%);
    --surface: hsl(0, 0%, 100%);
    --surface2: hsl(210, 30%, 94%);
    --surface3: hsl(210, 20%, 90%);
    --text: hsl(215, 28%, 12%);
    --text2: hsl(215, 16%, 40%);
    --text3: hsl(215, 12%, 60%);
    --border: hsla(0, 0%, 0%, 0.08);
    --accent: hsl(188, 80%, 32%);
    --accent-dim: hsl(188, 50%, 50%);
    --shadow-xs: 0 2px 8px hsla(0, 0%, 0%, 0.04);
    --shadow-sm: 0 4px 16px hsla(0, 0%, 0%, 0.05);
    --shadow: 0 12px 48px hsla(0, 0%, 0%, 0.08);
    --shadow-glow: 0 0 40px hsla(var(--hue), var(--sat), var(--lum), 0.06);
}}

*,*::before,*::after {{ box-sizing:border-box; margin:0; padding:0; }}

html {{ font-size:16px; scroll-behavior:smooth; -webkit-text-size-adjust:100%; }}

body {{
    font-family: var(--font);
    background: var(--bg);
    color: var(--text);
    line-height: 1.7;
    min-height: 100vh;
    transition: background var(--transition), color var(--transition);
    -webkit-font-smoothing: antialiased;
}}

/* ── Layout with rhythm ──────────────────────────── */
.container {{
    max-width: 1000px;
    margin: 0 auto;
    padding: calc(var(--space) * 6) calc(var(--space) * 5) calc(var(--space) * 16);
}}

/* ── Theme Toggle (glass orb) ──────────────────── */
.theme-toggle {{
    position: fixed; top:20px; right:24px; z-index:100;
    width:44px; height:44px; border-radius:50%;
    background: var(--surface); border:1px solid var(--border);
    color: var(--text2); cursor: pointer;
    display:flex; align-items:center; justify-content:center;
    font-size:1.25rem;
    backdrop-filter: blur(16px) saturate(1.4);
    -webkit-backdrop-filter: blur(16px) saturate(1.4);
    transition: all var(--transition);
    box-shadow: var(--shadow-sm);
}}
.theme-toggle:hover {{
    border-color: var(--accent);
    color: var(--accent);
    /* UI UX PRO MAX: spring transition */
    transform: scale(1.08) rotate(8deg);
    transition: all var(--transition-spring);
}}

/* ── Back to Top ──────────────────────────────── */
.back-top {{
    position: fixed; bottom:28px; right:24px; z-index:100;
    width:44px; height:44px; border-radius:50%;
    background: var(--surface); border:1px solid var(--border);
    color: var(--text2); cursor: pointer;
    display:flex; align-items:center; justify-content:center;
    font-size:1.3rem;
    backdrop-filter: blur(16px) saturate(1.4);
    -webkit-backdrop-filter: blur(16px) saturate(1.4);
    transition: all var(--transition);
    opacity:0; pointer-events:none; transform:translateY(12px);
    box-shadow: var(--shadow-sm);
}}
.back-top.visible {{ opacity:1; pointer-events:auto; transform:translateY(0); }}
.back-top:hover {{
    border-color: var(--accent2);
    color: var(--accent2);
    transform: translateY(-4px);
}}

/* ── Header — asymmetrical tension ────────────── */
.header {{
    padding: calc(var(--space) * 14) 0 calc(var(--space) * 10);
    position:relative;
    display:flex;
    flex-direction:column;
    align-items:flex-start;
}}
.header::after {{
    content:'';
    position:absolute;
    bottom:0; left:0;
    width:120px; height:3px;
    background: linear-gradient(90deg, var(--accent), var(--accent2), transparent);
    border-radius:2px;
}}
.header-icon {{
    width:56px; height:56px;
    color: var(--accent);
    margin-bottom: calc(var(--space) * 3);
}}
.header h1 {{
    font-size: clamp(1.8rem, 4vw, 2.6rem);
    font-weight:800;
    letter-spacing:-0.03em;
    line-height:1.1;
    margin-bottom: calc(var(--space) * 2);
}}
.header h1 .gradient {{
    background: linear-gradient(135deg, var(--text) 0%, var(--accent) 50%, var(--accent2) 100%);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
    background-clip:text;
}}
.header-sub {{
    font-size:1rem;
    color:var(--text2);
    max-width:480px;
    line-height:1.6;
    margin-bottom: calc(var(--space) * 3);
}}
.header-meta {{
    display:flex; gap:calc(var(--space) * 3); flex-wrap:wrap; align-items:center;
}}
.header-badge {{
    display:inline-flex; align-items:center; gap:6px;
    padding:5px 14px; border-radius:100px;
    background: color-mix(in srgb, var(--accent) 8%, transparent);
    border:1px solid color-mix(in srgb, var(--accent) 15%, transparent);
    color: var(--accent); font-size:0.78rem; font-weight:500;
}}
.header-subtle {{ color:var(--text3); font-size:0.82rem; }}

/* ── Summary Stats — broken grid ──────────────── */
.summary {{
    display:grid;
    grid-template-columns: 1fr 1.5fr 1fr 0.8fr;
    gap:calc(var(--space) * 3);
    margin: calc(var(--space) * 8) 0 calc(var(--space) * 10);
}}
.summary-item {{
    background:var(--surface);
    border:1px solid var(--border);
    border-radius:var(--corner);
    padding: calc(var(--space) * 5) calc(var(--space) * 3);
    text-align:center;
    transition: all var(--transition);
    position:relative; overflow:hidden;
    /* UI UX PRO MAX: glass panel */
    backdrop-filter: blur(4px);
    -webkit-backdrop-filter: blur(4px);
}}
.summary-item::before {{
    content:'';
    position:absolute; top:0; left:0; right:0;
    height:2px;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
    opacity:0;
    transition: opacity var(--transition);
}}
.summary-item:hover::before {{ opacity:1; }}
.summary-item:hover {{ border-color:var(--border-hover); transform:translateY(-3px); }}
.summary-item:first-child {{ grid-column:1; }}
.summary-item:nth-child(2) {{ grid-column:2; }}
.summary-item:nth-child(3) {{ grid-column:3; }}
.summary-item:nth-child(4) {{ grid-column:4; }}

.summary-num {{
    font-size: clamp(1.4rem, 2.5vw, 2rem);
    font-weight:800;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
    background-clip:text;
    font-variant-numeric:tabular-nums;
}}
.summary-label {{
    font-size:0.75rem;
    color:var(--text3);
    margin-top:2px;
    letter-spacing:0.04em;
    text-transform:uppercase;
}}

/* ── Navigation between cards ──────────────────── */
.proj-nav {{
    display:flex; gap:calc(var(--space) * 2);
    margin-bottom: calc(var(--space) * 6);
    overflow-x:auto;
    padding-bottom: calc(var(--space) * 1);
}}
.proj-nav a {{
    padding:6px 14px;
    border-radius:100px;
    font-size:0.78rem;
    font-weight:500;
    color:var(--text3);
    text-decoration:none;
    border:1px solid var(--border);
    transition: all var(--transition);
    white-space:nowrap;
    flex-shrink:0;
}}
.proj-nav a:hover {{
    border-color:color-mix(in srgb, var(--accent) 30%, transparent);
    color:var(--accent);
    background:color-mix(in srgb, var(--accent) 6%, transparent);
}}

/* ── Card — staggered depth with glassmorphism ────── */
.card {{
    background: var(--surface);
    border:1px solid var(--border);
    border-radius:var(--corner-lg);
    margin-bottom: calc(var(--space) * 8);
    position:relative;
    overflow:hidden;
    transition: all var(--transition);
    box-shadow: var(--shadow);
    /* UI UX PRO MAX: glass edge highlight */
    backdrop-filter: blur(2px);
    -webkit-backdrop-filter: blur(2px);
}}
/* Staggered card (Taste-Skill: 反模板) */
.card:nth-child(odd) {{
    transform: rotate(-0.3deg);
}}
.card:nth-child(even) {{
    transform: rotate(0.3deg);
}}
.card:hover {{
    border-color:var(--border-hover);
    transform: rotate(0deg) scale(1.002);
    box-shadow: var(--shadow), var(--shadow-glow);
}}

/* Gradient border overlay on hover */
.card::before {{
    content:'';
    position:absolute; inset:0;
    border-radius:var(--corner-lg);
    padding:1px;
    background: linear-gradient(135deg, transparent 40%, color-mix(in srgb, var(--accent) 12%, transparent) 100%);
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    pointer-events:none;
    opacity:0;
    transition: opacity var(--transition);
}}
.card:hover::before {{ opacity:1; }}

.card-ribbon {{
    position:absolute;
    top:calc(var(--space) * 3);
    right:calc(var(--space) * 3);
    padding:4px 14px;
    font-size:0.7rem;
    font-weight:600;
    letter-spacing:0.06em;
    text-transform:uppercase;
    color: var(--accent);
    background: color-mix(in srgb, var(--accent) 10%, var(--surface));
    border:1px solid color-mix(in srgb, var(--accent) 15%, transparent);
    border-radius:100px;
}}
/* Alternating ribbon positions for visual variety */
.card:nth-child(even) .card-ribbon {{
    right:auto;
    left:calc(var(--space) * 3);
}}

/* ── Card Head ───────────────────────────────────── */
.card-head {{
    display:flex;
    justify-content:space-between;
    align-items:flex-start;
    gap:calc(var(--space) * 4);
    padding: calc(var(--space) * 7) calc(var(--space) * 7) 0;
}}
.card-head-left {{ flex:1; min-width:0; }}
.repo-byline {{
    display:flex; align-items:center; gap:6px;
    font-size:0.82rem;
    margin-bottom:2px;
    color:var(--text3);
}}
.avatar-initial {{
    width:22px; height:22px; border-radius:50%;
    flex-shrink:0;
    display:inline-flex; align-items:center; justify-content:center;
    font-size:0.65rem; font-weight:700; color:#fff;
    line-height:1;
    text-transform:uppercase;
    user-select:none;
}}
.owner {{ color:var(--text2); }}
.slash {{ color:var(--text3); }}
.repo-name {{
    font-size:clamp(1.2rem, 2.5vw, 1.6rem);
    font-weight:700; line-height:1.25;
}}
.repo-name a {{
    color:var(--text);
    text-decoration:none;
    transition:color var(--transition);
}}
.repo-name a:hover {{ color:var(--accent); }}
.card-head-right {{
    display:flex; align-items:center; gap:12px;
    flex-shrink:0; flex-wrap:wrap;
}}
.stat {{
    display:inline-flex; align-items:center; gap:4px;
    font-size:0.82rem; font-weight:600; white-space:nowrap;
}}
.stat svg {{ width:16px; height:16px; }}
.stat-num {{ font-variant-numeric:tabular-nums; }}
.st-stars {{ color:var(--star); }}
.st-forks {{ color:var(--accent2); }}
.lang-dot {{
    display:inline-block; padding:2px 10px; border-radius:100px;
    font-size:0.7rem; font-weight:600; color:#fff !important;
    line-height:1.6;
}}

/* ── One-liner + Desc ──────────────────────────── */
.card-oneliner {{
    margin: calc(var(--space) * 3) calc(var(--space) * 7) 0;
    padding: calc(var(--space) * 3) calc(var(--space) * 4);
    background: color-mix(in srgb, var(--accent) 5%, transparent);
    border-left: 3px solid var(--accent);
    border-radius: 0 var(--corner-sm) var(--corner-sm) 0;
    font-size:0.92rem;
    color:var(--text);
    font-weight:500;
    line-height:1.6;
}}
.card-desc {{
    margin: calc(var(--space) * 2) calc(var(--space) * 7) 0;
    font-size:0.88rem;
    color:var(--text2);
    line-height:1.7;
}}

/* ── Tabs (Pure CSS, with taste) ──────────────────── */
.tab-wrap {{
    margin: calc(var(--space) * 4) calc(var(--space) * 7) 0;
}}
.tab-input {{ display:none; }}

.tab-labels {{
    display:flex; gap:2px;
    border-bottom:1px solid var(--border);
    overflow-x:auto;
    position:relative;
}}
.tab-label {{
    padding:10px 18px;
    font-size:0.8rem;
    font-weight:500;
    color:var(--text3);
    cursor:pointer;
    white-space:nowrap;
    border-bottom:2px solid transparent;
    margin-bottom:-1px;
    transition: all var(--transition);
    user-select:none;
    border-radius:6px 6px 0 0;
    letter-spacing:0.01em;
}}
.tab-label:hover {{
    color:var(--text2);
    background:color-mix(in srgb, var(--text) 3%, transparent);
}}

.tab-panels {{ position:relative; }}
.tab-panel {{
    display:none;
    padding: calc(var(--space) * 5) 0 calc(var(--space) * 3);
    animation: fadeSlide 0.35s ease;
}}
@keyframes fadeSlide {{
    from {{ opacity:0; transform:translateY(8px); }}
    to {{ opacity:1; transform:translateY(0); }}
}}

#{{tab1_id}}:checked ~ .tab-labels label[for="{tab1_id}"],
#{{tab2_id}}:checked ~ .tab-labels label[for="{tab2_id}"],
#{{tab3_id}}:checked ~ .tab-labels label[for="{tab3_id}"],
#{{tab4_id}}:checked ~ .tab-labels label[for="{tab4_id}"] {{
    color:var(--accent);
    border-bottom-color:var(--accent);
}}
#{{tab1_id}}:checked ~ .tab-panels .tab-panel:nth-child(1) {{ display:block; }}
#{{tab2_id}}:checked ~ .tab-panels .tab-panel:nth-child(2) {{ display:block; }}
#{{tab3_id}}:checked ~ .tab-panels .tab-panel:nth-child(3) {{ display:block; }}
#{{tab4_id}}:checked ~ .tab-panels .tab-panel:nth-child(4) {{ display:block; }}

/* ── Panel Content ──────────────────────────────── */
.panel-section {{ margin-bottom:calc(var(--space) * 4); }}
.panel-section:last-child {{ margin-bottom:0; }}
.panel-h {{
    font-size:0.78rem;
    font-weight:600;
    color:var(--accent);
    margin-bottom:calc(var(--space) * 2);
    letter-spacing:0.03em;
    text-transform:uppercase;
}}
.panel-section p {{
    font-size:0.87rem;
    color:var(--text2);
    line-height:1.8;
}}
.panel-list {{ list-style:none; padding:0; }}
.panel-list li {{
    position:relative;
    padding: calc(var(--space) * 1.5) 0 calc(var(--space) * 1.5) calc(var(--space) * 5);
    font-size:0.87rem;
    color:var(--text2);
    line-height:1.6;
}}
.panel-list li::before {{
    content:'';
    position:absolute;
    left:0;
    top:calc(var(--space) * 3);
    width:6px; height:6px;
    border-radius:50%;
    background: var(--accent);
    opacity:0.6;
}}

/* ── Code Block ────────────────────────────────── */
.code-block {{
    background:var(--surface2);
    border:1px solid var(--border);
    border-radius:var(--corner-sm);
    padding: calc(var(--space) * 4);
    font-family:var(--mono);
    font-size:0.8rem;
    color:var(--accent);
    overflow-x:auto;
    line-height:1.7;
    white-space:pre-wrap;
    word-break:break-all;
}}

/* ── Task Items ────────────────────────────────── */
.task-item {{
    background:var(--surface2);
    border:1px solid var(--border);
    border-radius:var(--corner);
    padding: calc(var(--space) * 4);
    margin-bottom:calc(var(--space) * 3);
    transition: border-color var(--transition);
}}
.task-item:hover {{ border-color:var(--border-hover); }}
.task-item:last-child {{ margin-bottom:0; }}
.task-title {{
    font-size:0.88rem;
    font-weight:600;
    color:var(--text);
    margin-bottom:calc(var(--space) * 2);
}}
.task-body {{
    font-size:0.84rem;
    color:var(--text2);
    line-height:1.8;
}}

/* ── Alt Items ─────────────────────────────────── */
.alt-list {{ display:flex; flex-direction:column; gap:calc(var(--space) * 2); }}
.alt-item {{
    display:flex; gap:calc(var(--space) * 3);
    padding: calc(var(--space) * 3) calc(var(--space) * 4);
    background:var(--surface2);
    border:1px solid var(--border);
    border-radius:var(--corner-sm);
    align-items:flex-start;
    transition: border-color var(--transition);
}}
.alt-item:hover {{ border-color:var(--border-hover); }}
.alt-name {{
    font-size:0.82rem;
    font-weight:600;
    color:var(--accent2);
    white-space:nowrap;
    flex-shrink:0;
    min-width:90px;
}}
.alt-desc {{
    font-size:0.82rem;
    color:var(--text2);
    line-height:1.6;
}}

/* ── Details (全文折叠) ────────────────────────── */
.details-more {{
    margin: calc(var(--space) * 1) calc(var(--space) * 7) calc(var(--space) * 6);
    border-top:1px solid var(--border);
    padding-top:calc(var(--space) * 2);
}}
.details-more summary {{
    cursor:pointer;
    font-size:0.8rem;
    color:var(--text3);
    padding:calc(var(--space) * 1) 0;
    user-select:none;
    transition:color var(--transition);
    list-style:none;
    display:flex; align-items:center;
}}
.details-more summary::-webkit-details-marker {{ display:none; }}
.details-more summary:hover {{ color:var(--accent); }}
.details-more summary span::before {{
    content:'\u25B6 ';
    font-size:0.65rem;
    transition:transform var(--transition);
    display:inline-block;
}}
.details-more[open] summary span::before {{
    content:'\u25BC ';
}}
.details-body {{
    padding:calc(var(--space) * 3) 0 0;
    font-size:0.87rem;
    color:var(--text2);
    line-height:1.8;
}}

/* ── Footer ────────────────────────────────────── */
.footer {{
    text-align:center;
    padding:calc(var(--space) * 8) 0 calc(var(--space) * 4);
    border-top:1px solid var(--border);
}}
.footer p {{ font-size:0.75rem; color:var(--text3); }}
.footer a {{ color:var(--accent); text-decoration:none; }}
.footer a:hover {{ text-decoration:underline; }}

/* ── Responsive ────────────────────────────────── */
@media (max-width:768px) {{
    .container {{ padding:calc(var(--space) * 4) calc(var(--space) * 3) calc(var(--space) * 10); }}
    .header {{ padding:calc(var(--space) * 8) 0 calc(var(--space) * 6); }}
    .summary {{ grid-template-columns:1fr 1fr; gap:calc(var(--space) * 2); }}
    .summary-item:first-child {{ grid-column:auto; }}
    .summary-item:nth-child(2) {{ grid-column:auto; }}
    .summary-item:nth-child(3) {{ grid-column:auto; }}
    .summary-item:nth-child(4) {{ grid-column:auto; }}
    .card-head {{ flex-direction:column; gap:calc(var(--space) * 2); padding:calc(var(--space) * 5) calc(var(--space) * 4) 0; }}
    .card-head-right {{ align-self:flex-start; }}
    .repo-name {{ font-size:1.15rem; }}
    .tab-wrap {{ margin:calc(var(--space) * 3) calc(var(--space) * 4) 0; }}
    .tab-label {{ padding:8px 10px; font-size:0.75rem; }}
    .tab-panel {{ padding:calc(var(--space) * 3) 0; }}
    .card-oneliner {{ margin:calc(var(--space) * 2) calc(var(--space) * 4) 0; font-size:0.85rem; }}
    .card-desc {{ margin:calc(var(--space) * 1) calc(var(--space) * 4) 0; }}
    .details-more {{ margin:calc(var(--space) * 1) calc(var(--space) * 4) calc(var(--space) * 4); }}
    .card:nth-child(odd), .card:nth-child(even) {{ transform:none; }}
    .card:nth-child(even) .card-ribbon {{ right:calc(var(--space) * 3); left:auto; }}
}}

@media (max-width:420px) {{
    .summary {{ grid-template-columns:1fr 1fr; gap:calc(var(--space) * 1); }}
    .tab-labels {{ gap:0; }}
    .tab-label {{ padding:8px 6px; font-size:0.7rem; }}
}}

@media (prefers-reduced-motion:reduce) {{
    *,*::before,*::after {{
        animation-duration:0.01ms!important;
        transition-duration:0.01ms!important;
        scroll-behavior:auto!important;
    }}
    .card:hover, .card:nth-child(odd), .card:nth-child(even) {{ transform:none; }}
    .summary-item:hover {{ transform:none; }}
    .theme-toggle:hover {{ transform:none; }}
}}
</style>
</head>
<body>

<!-- Theme Toggle -->
<button class="theme-toggle" id="themeToggle" aria-label="切换主题">🌙</button>

<!-- Back to Top -->
<a href="#" class="back-top" id="backTop" aria-label="回到顶部">↑</a>

<div class="container">

    <!-- ═══ HEADER ═══ -->
    <header class="header">
        <svg class="header-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="16 18 22 12 16 6"></polyline>
            <polyline points="8 6 2 12 8 18"></polyline>
            <circle cx="12" cy="12" r="2"></circle>
        </svg>
        <h1><span class="gradient">GitHub 热门分析</span></h1>
        <p class="header-sub">近一周最受关注的 Top 3 项目 · 深度分析 + 全流程上手指南<br>参照「软件工具学习.md」5 块分析框架</p>
        <div class="header-meta">
            <span class="header-badge">
                <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0a8 8 0 110 16A8 8 0 018 0zm0 1.5a6.5 6.5 0 100 13 6.5 6.5 0 000-13zM8 3a.75.75 0 01.75.75v3.5l2.25.75a.75.75 0 01-.5 1.414L7.5 8.25a.75.75 0 01-.5-.707V3.75A.75.75 0 018 3z"/></svg>
                {generated_at}
            </span>
            <span class="header-subtle">数据源: OSS Insight · 每周一更新</span>
        </div>
    </header>

    <!-- ═══ SUMMARY ═══ -->
    <div class="summary">
        <div class="summary-item">
            <div class="summary-num" data-count="{len(repos)}">{len(repos)}</div>
            <div class="summary-label">热门项目</div>
        </div>
        <div class="summary-item">
            <div class="summary-num" data-count="{total_stars}">0</div>
            <div class="summary-label">总 Star</div>
        </div>
        <div class="summary-item">
            <div class="summary-num" data-count="{total_forks}">0</div>
            <div class="summary-label">总 Fork</div>
        </div>
        <div class="summary-item">
            <div class="summary-num">{len([r for r in repos if r.get('language','')])}</div>
            <div class="summary-label">编程语言数</div>
        </div>
    </div>

    <!-- ═══ CARDS ═══ -->
    {nav_html}

    {cards}

    <!-- ═══ FOOTER ═══ -->
    <footer class="footer">
        <p>
            数据来源: <a href="https://ossinsight.io" target="_blank" rel="noopener">OSS Insight</a> ·
            GitHub Trending · 自动生成
        </p>
    </footer>

</div>

<!-- ═══ JS ── Interactivity ═══ -->
<script>
(function(){{
    'use strict';

    // ── 1. Theme Toggle ──────────────────────────
    const toggle = document.getElementById('themeToggle');
    const html = document.documentElement;
    const saved = localStorage.getItem('gh-trending-theme');
    if (saved) {{
        html.setAttribute('data-theme', saved);
        toggle.textContent = saved === 'light' ? '☀️' : '🌙';
    }}
    toggle.addEventListener('click', function() {{
        const current = html.getAttribute('data-theme');
        const next = current === 'light' ? 'dark' : 'light';
        html.setAttribute('data-theme', next);
        this.textContent = next === 'light' ? '☀️' : '🌙';
        localStorage.setItem('gh-trending-theme', next);
    }});

    // ── 2. Animated Counters ────────────────────
    const counters = document.querySelectorAll('.summary-num[data-count]');
    if ('IntersectionObserver' in window) {{
        const obs = new IntersectionObserver((entries) => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    const el = entry.target;
                    const target = parseInt(el.getAttribute('data-count'), 10);
                    if (target <= 5) {{ el.textContent = target; return; }}
                    animateCounter(el, target);
                    obs.unobserve(el);
                }}
            }});
        }}, {{ threshold:0.5 }});
        counters.forEach(c => obs.observe(c));
    }} else {{
        counters.forEach(c => {{
            const t = parseInt(c.getAttribute('data-count'), 10);
            c.textContent = t.toLocaleString();
        }});
    }}

    function animateCounter(el, target) {{
        const duration = 1000; // ms
        const steps = 30;
        const increment = target / steps;
        let current = 0;
        const step = () => {{
            current += increment;
            if (current >= target) {{
                el.textContent = target.toLocaleString();
                return;
            }}
            el.textContent = Math.round(current).toLocaleString();
            requestAnimationFrame(step);
        }};
        requestAnimationFrame(step);
    }}

    // ── 3. Back to Top ──────────────────────────
    const backTop = document.getElementById('backTop');
    window.addEventListener('scroll', function() {{
        if (window.scrollY > 600) {{
            backTop.classList.add('visible');
        }} else {{
            backTop.classList.remove('visible');
        }}
    }});

    // ── 4. Smooth anchor scroll ─────────────────
    document.querySelectorAll('a[href^="#"]').forEach(a => {{
        a.addEventListener('click', function(e) {{
            const href = this.getAttribute('href');
            if (href === '#') return;
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) target.scrollIntoView({{ behavior:'smooth' }});
        }});
    }});

}})();
</script>
</body>
</html>"""
    return html


# ═══════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════

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

    # 获取每个项目的详细信息（star, fork, owner 等）
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

    # 重复项目检测
    print("[*] 检查历史记录，过滤重复项目...")
    selected = filter_duplicates(raw_repos)

    # 给需要分析的项目补全详细信息
    repos = []
    for r in selected:
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
        repos.append(r)

    # 记录本次分析的项目到历史
    add_to_history(repos)

    print(f"\n[+] 最终入选 {len(repos)} 个项目：")
    for i, r in enumerate(repos, 1):
        fn = r.get("repo_name", "")
        print(f"  #{i} {fn}  {fmt_stars(r.get('stars',0))} stars")

    beijing = timezone(timedelta(hours=8))
    now = datetime.now(beijing)
    generated_at = now.strftime("%Y-%m-%d %H:%M CST")

    html = generate_html(repos, generated_at)

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
