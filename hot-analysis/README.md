# GitHub 开源项目深度分析引擎

> **三种模式**：热门趋势分析 · 单项目指定分析 · 科普素材一键生成
>
> AI Agent Skill — 输出带 9 项交互特性的深色极简风 HTML 分析报告

---

## 什么是这个项目？

这是一个 **AI Agent Skill**，围绕 GitHub 开源项目分析提供三种工作模式：

### 🔥 模式一：热门趋势分析
每周自动抓取 GitHub Trending 近一周 Top 3 热门开源项目，参照**5 块分析框架**深度解析，输出带交互的深色极简风 HTML 报告。内置**重复项目检测机制**——已分析过的项目再次出现时自动跳过，除非 Star 显著增长（≥30% 或 ≥500）。

### 🎯 模式二：单项目指定分析
用户指定任意 GitHub 项目（`owner/repo` 或完整 GitHub URL），AI 获取项目元数据后按相同的 5 块框架撰写深度分析，生成同款交互 HTML 报告。

### 📦 模式三：科普素材生成
基于分析报告，为每个项目自动生成两套内容素材：
- **GPT-image2 生图提示词**（英文，100-200 词，9:16 竖版科普信息卡）
- **口播文案**（中文，~300 字短视频脚本）

输出按分类目录打包，直接可用。

---

## 效果预览

### HTML 报告
| 特性 | 说明 |
|------|------|
| 分析 3 个项目（或单个指定项目） | 每个含 5 个 Tab（这是什么 / 快速上手 / 真实任务 / 同类对比 / 暗坑与进阶） |
| 深色极简风 | 玻璃拟态卡片 + 青色(#22d3ee)靛蓝(#818cf8)主色调 |
| 明暗主题切换 | 点击右上角按钮切换亮色/暗色模式，localStorage 持久化 |
| 统计数字动画 | IntersectionObserver 驱动的计数器滚动入场 |
| 折叠全文 | details/summary 查看完整分析原文 |
| 浮动回到顶部 | 滚动超 600px 显示 |
| 响应式布局 | 768px / 420px 双断点适配移动端 |
| 无障碍支持 | prefers-reduced-motion |

### 素材输出
```
素材输出_20260608_1437/
├── 00_本期概览.md
├── 【HTML报告】/latest.html
├── 【项目提示词】/
│   ├── 01_项目A_prompt.md    ← GPT-image2 生图提示词（9:16 竖版）
│   └── ...
└── 【口播文案】/
    ├── 01_项目A_script.md    ← ~300 字短视频口播稿
    └── ...
```

---

## 快速开始

### 环境要求
- Python 3.8+（标准库即可，无需第三方包）
- 网络可访问 `ossinsight.io`
- Windows / macOS / Linux 均可
- **Windows 注意**：使用 `python` 命令而非 `python3`（WindowsApps 版会报 exit 49）

### 安装

```bash
# 克隆仓库
git clone https://github.com/youyituomaoxian/laobanjiu-skills.git
cd laobanjiu-skills/hot-analysis

# 直接运行（纯标准库，无需 pip install）
```

### 运行热门分析

```bash
python scripts/github_trending_weekly.py
```

脚本会自动：
1. 调用 OSS Insight API 获取近一周 Top 10 候选项目
2. 检查历史记录（`output/analysis_history.json`），过滤已分析且无重大更新的项目
3. 对最终 3 个项目进行深度分析（5 块框架）
4. 生成交互式 HTML 报告到 `output/` 目录

完成后会询问是否继续生成科普素材。

### 运行单项目分析

```bash
# 通过 owner/repo 指定项目
python scripts/fetch_repo_info.py owner/repo

# 也支持完整 GitHub URL
python scripts/fetch_repo_info.py https://github.com/owner/repo
```

脚本输出项目元数据 JSON 到 `output/_repo_owner_repo.json`，然后 AI 按 5 块框架撰写深度分析，生成同名交互 HTML 报告。

### 生成素材

热门分析完成后自动询问，也可单独触发：

```bash
python scripts/generate_material.py
```

素材脚本会解析 `output/latest.html`，提取项目元数据并创建分类目录结构，由 AI 创作提示词和口播文案。

---

## 目录结构

```
hot-analysis/
├── README.md                            ← 本文件
├── SKILL.md                             ← Agent Skill 定义（标准 Open Agent Skill 格式）
├── CLAUDE.md                            ← AI Agent 项目规则
├── reference/
│   └── 软件工具学习.md                  ← 5 块分析框架参考文档
├── scripts/
│   ├── github_trending_weekly.py        ← 热门分析主脚本（抓取 + 去重 + HTML 生成）
│   ├── fetch_repo_info.py               ← 单项目元数据获取（OSS Insight API）
│   └── generate_material.py             ← 素材生成辅助脚本（目录创建 + 数据提取）
└── output/                              ← 所有输出文件
    ├── github_hot_analysis_YYYYMMDD_HHMM.html   # 批量分析报告
    ├── analyze_owner_repo_YYYYMMDD_HHMM.html    # 单项目分析报告
    ├── latest.html                               # 最新报告（始终覆盖）
    ├── _repo_owner_repo.json                     # 单项目元数据缓存
    ├── analysis_history.json                     # 重复检测历史（60 天自动过期）
    └── 素材输出_YYYYMMDD_HHMM/                   # 素材包（可选生成）
        ├── 00_本期概览.md
        ├── _projects.json
        ├── 【HTML报告】/
        ├── 【项目提示词】/
        └── 【口播文案】/
```

---

## 分析框架

每个项目按照 **5 块结构**深度解析，展示为 5 个 Tab：

### ① 这是什么
- **一句话说清** — 用最通俗的话定义工具的核心价值
- **它消灭了什么麻烦** — 之前同样的工作有多痛苦
- **最适合的 3 个场景** — 谁在什么情况下用它
- **绝对不适合做什么** — 防止硬用它做不擅长的事

### ② 快速上手
- **最简安装** — 一行命令 + 验证方式
- **第一个成功操作** — 看到什么提示说明成功了
- **实用技巧** — 老手才知道的捷径

### ③ 真实任务
3 个典型任务（难度递进），每个包含：
- **以前怎么做** vs **用这个工具怎么做** 的直观对比
- 完整步骤 + 预期结果
- 常见卡点

### ④ 同类对比
- 相似工具怎么选（对话式对比，不是参数表）
- 黄金搭档推荐（组合使用示例）

### ⑤ 暗坑与进阶信号
- **反人类设计** — 最常被骂的三个设计
- **常见误区** — 广泛流传但其实是错的用法
- **进阶信号** — 怎么判断自己已经「会用」了
- **下一步资源** — 官方文档章节、必读教程、社区推荐

---

## 设计系统

双设计体系叠加，确保每一个输出的页面具有一致的视觉品质。

### 🎨 Taste-Skill 审美原则
- HSL 变量化色彩体系（`--hue / --sat / --lum`），改色相全局变色
- Type Scale 1.25（Major Third）
- 4px 间距网格
- 卡片交错旋转 ±0.3deg（破模板感）
- 三级表面质感（surface / surface2 / surface3）
- 渐变边框悬停叠加层

### ✨ UI UX PRO MAX 交互体系
- 玻璃拟态卡片（backdrop-filter + 边缘高光）
- 弹性 spring 过渡动效（`cubic-bezier(0.34, 1.56, 0.64, 1)`）
- 多层阴影体系（shadow-xs / shadow-sm / shadow-glow）
- 三级圆角体系（--corner-sm: 8px / --corner-md: 14px / --corner-lg: 20px）

---

## 重复项目检测

避免反复分析同一批项目的机制：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| FETCH_TOP_N | 10 | 每次抓取 10 个候选项目 |
| MAX_REPOS | 3 | 最终深度分析 3 个 |
| STAR_GROWTH_RATE | 0.30 | Star 增长 ≥30% 视为重大更新 |
| STAR_GROWTH_ABSOLUTE | 500 | Star 增长 ≥500 重新纳入 |
| HISTORY_DAYS_IGNORE | 60 | 60 天前的记录自动过期 |

逻辑：
1. 从未分析过的项目 → 直接入选
2. 分析过但 Star 显著增长 → 重新分析
3. 分析过且无明显变化 → 跳过
4. 跳过项目太多导致不足 3 个 → 按热度补回

---

## 输出规范

### HTML 报告
- 批量分析：`output/github_hot_analysis_YYYYMMDD_HHMM.html`
- 单项目：`output/analyze_owner_repo_YYYYMMDD_HHMM.html`
- 最新指针：`output/latest.html`（始终覆盖为最新生成）
- 交互特性：9 项（见上文）

### 生图提示词
- 语言：英文
- 长度：100-200 词
- 比例：9:16 竖版（适合手机短视频/Reels）
- 风格：科普信息卡 / 科技插画 / 数据可视化
- 要素：视觉风格 + 核心构图 + 配色方案 + 字体排版 + 数据元素

### 口播文案
- 语言：中文
- 长度：250-300 字（约 1 分钟语速）
- 结构：痛点开头 → 一句话定位 → 核心亮点 → 使用场景 → 收尾

---

## 作为 Agent Skill 使用

如果你使用支持 **Open Agent Skill 规范**的 AI 编程助手（如 Claude Code、OpenClaw 等），只需：

1. 将 `scripts/` 和 `reference/` 放到你的项目目录
2. 将 `CLAUDE.md` 放到项目根目录（AI 自动读取）
3. 将 `SKILL.md` 注册到 AI Skill 系统

三步完成，AI 即可响应以下指令：

| 指令 | 触发词 | 行为 |
|------|--------|------|
| 热门分析 | 「热门分析」「分析热门项目」 | 抓取 → 去重 → 分析 Top 3 → 生成 HTML |
| 单项目分析 | 「分析项目 owner/repo」或 GitHub URL | 获取元数据 → AI 分析 → 生成 HTML |
| 素材生成 | 「生成素材」「热门素材」 | 解析最新报告 → 生成提示词 + 口播文案 |

---

## 常见问题

**Q: 需要 GitHub Token 吗？**
A: 不需要。所有数据来自 OSS Insight API（免费、无需认证）。

**Q: GitHub API 被墙怎么办？**
A: OSS Insight API 本身就是替代方案。GitHub raw content 和 API 在某些地区不可达，本项目全程使用 OSS Insight。

**Q: 为什么不用 `python3` 命令？**
A: Windows 下 WindowsApps 版本的 python3 会报 exit code 49。请用 `python` 命令。

**Q: 单项目分析和热门分析有什么区别？**
A: 热门分析自动抓取 Trendng 项目并去重；单项目分析由用户指定任意项目。分析框架和 HTML 输出格式完全一致。

**Q: 能分析几个项目？**
A: 热门分析默认深度分析 3 个（候选池 10 个），可在脚本中修改 `MAX_REPOS` 和 `FETCH_TOP_N`。单项目分析每次一个。

**Q: 素材内容是 AI 生成的还是模板？**
A: 目录结构由脚本创建，生图提示词和口播文案需要 AI 创作（模板做不到高质量）。

**Q: 如何自定义设计配色？**
A: 修改 HTML 生成逻辑中的 CSS 变量 `--hue` / `--sat` / `--lum`。改色相即可全局变色。

---

## License

MIT
