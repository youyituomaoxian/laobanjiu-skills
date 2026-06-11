# laobanjiu-skills

> AI Agent Skill 合集 — 自用工作流，打包成标准 Open Agent Skill 格式，方便复用和分享。

---

## 📊 hot-analysis — GitHub 开源项目深度分析引擎

一条指令，**三种模式**：抓取热门趋势、指定项目深度分析、一键生成科普素材。全部输出**带交互的深色极简风 HTML 报告**。

> v2 更新：单项目分析新增 README 内容获取 + 分析深度选择 + 双输出（HTML 长页面 + 自适应卡片）

### 核心能力

| 模式 | 触发方式 | 产出 |
|------|---------|------|
| 🔥 **热门趋势分析** | 用户说「热门分析」 | 抓取 GitHub Trending Top 3 项目，去重检测后深度分析，输出交互 HTML 报告 |
| 🎯 **单项目指定分析** | 用户说「分析项目 owner/repo」或粘贴 GitHub URL | 指定任意项目获取元数据，AI 按 5 块框架深度分析，输出同款 HTML 报告 |
| 📦 **素材一键生成** | 在热门分析完成后自动询问，或说「生成素材」 | 为每个项目生成 GPT-image2 生图提示词（英文，9:16 竖版）+ 300 字口播文案（中文），打包到分类目录 |

### 交互式 HTML 报告特性

生成的报告不是静态文档，而是**带完整交互的独立 HTML 页面**：

- **5 个 Tab 切换** — 这是什么 / 快速上手 / 真实任务 / 同类对比 / 暗坑与进阶（CSS-only radio hack，零依赖）
- **明暗主题切换** — localStorage 持久化偏好
- **统计数字滚动动画** — IntersectionObserver 驱动的计数器
- **折叠全文** — details/summary 元素查看完整分析
- **浮动回到顶部** — 滚动超 600px 显示
- **响应式设计** — 768px / 420px 双断点适配移动端
- **无障碍支持** — prefers-reduced-motion

### 视觉设计系统

双重设计体系叠加，确保每一个输出的页面都具有一致性：

**🎨 Taste-Skill 审美体系：**
- HSL 变量化色彩（`--hue/--sat/--lum`），一次改色相全局变色
- Type Scale 1.25 Major Third 字体层级
- 4px 间距网格
- 卡片交错旋转 ±0.3deg 打破模板感
- 三级表面质感递进（surface/surface2/surface3）

**✨ UI UX PRO MAX 工程体系：**
- 玻璃拟态卡片（backdrop-filter + 边缘高光）
- 弹性 spring 动效（`cubic-bezier(0.34, 1.56, 0.64, 1)`）
- 多层阴影体系（shadow-xs/sm/glow）
- 三级圆角体系（--corner-sm: 8px / --corner-md: 14px / --corner-lg: 20px）

### 分析框架

每个项目按 **5 块结构**深度解析，严格参照 `reference/软件工具学习.md`：

1. **这是什么** — 一句话定义 + 消灭了什么麻烦 + 最适合的 3 个场景 + 绝对不适合做的事
2. **快速上手** — 最简安装命令 + 第一个成功操作验证 + 实用技巧
3. **真实任务** — 3 个典型任务（以前怎么做 vs 用这个工具怎么做）难度递进
4. **同类对比** — 相似工具选择建议 + 黄金搭档推荐
5. **暗坑与进阶信号** — 反人类设计 + 常见误区 + 进阶学习资源

### 快速开始

```bash
# 克隆
git clone https://github.com/youyituomaoxian/laobanjiu-skills.git
cd laobanjiu-skills/hot-analysis

# 模式一：热门分析（自动抓取 + 去重 + 深度分析 Top 3）
python scripts/github_trending_weekly.py

# 模式二：指定项目分析（获取元数据，AI 后续生成 HTML 报告）
python scripts/fetch_repo_info.py owner/repo
python scripts/fetch_repo_info.py https://github.com/owner/repo

# 模式三：素材生成（基于最新报告，AI 生成提示词 + 口播文案）
python scripts/generate_material.py
```

### 输出目录结构

```
hot-analysis/
├── output/
│   ├── github_hot_analysis_YYYYMMDD_HHMM.html    # 批量分析报告
│   ├── analyze_owner_repo_YYYYMMDD_HHMM.html     # 单项目分析报告
│   ├── latest.html                                # 最新报告（始终覆盖为最新）
│   ├── _repo_owner_repo.json                      # 单项目元数据缓存（AI 读取用）
│   ├── analysis_history.json                      # 重复检测历史（60 天自动过期）
│   └── 素材输出_YYYYMMDD_HHMM/                    # 素材包（可选生成）
│       ├── 00_本期概览.md
│       ├── _projects.json
│       ├── 【HTML报告】/
│       ├── 【项目提示词】/
│       └── 【口播文案】/
├── scripts/
│   ├── github_trending_weekly.py  # 热门抓取 + 去重 + HTML 生成
│   ├── fetch_repo_info.py         # 单项目元数据获取（OSS Insight API）
│   └── generate_material.py       # 素材目录创建 + 数据提取
├── reference/
│   └── 软件工具学习.md              # 5 块分析框架参考文档
├── SKILL.md                       # Open Agent Skill 定义
└── CLAUDE.md                      # AI 项目规则（Agent 自动读取）
```

### 数据来源

- **OSS Insight API**（`https://ossinsight.io/api/mcp`）— 免费，无需 Token
- GitHub API 和 raw content 在某些地区不可达，OSS Insight 是替代方案

### 注意事项

- **Windows**: 使用 `python` 命令而非 `python3`（WindowsApps 版 python3 会报 exit 49）
- **网络**: 需要能够访问 `ossinsight.io` API
- **去重**: 已分析过的项目再次出现时会自动跳过，除非 Star 增长 ≥30% 或 ≥500
- **素材**: 提示词和口播文案由 AI 根据分析数据创作，脚本只负责目录结构和数据提取

---

## 🔬 hot-compare — GitHub 项目横向对比 Skill

一条指令，对比 2-5 个 GitHub 项目，按 **5 模块优化版方法论** 一步到位输出对比报告 + 卡片 + 素材。

### 5 模块结构

| 模块 | 内容 | 让你获得什么 |
|------|------|------------|
| ① 单项深解 | 每项目 7 项分析（+上手路径）| 彻底了解每个项目 |
| ② 矩阵对比 | 10 行表格 + 决策指引 | 快速做出选型决定 |
| ③ 场景对抗 | 3 个真实场景下的操作对比 | 学会实际使用 |
| ④ 组合串联 | 原生组合 + 非兼容串联方案 | 学会多工具联动 |
| ⑤ 高手路径 | 入门→会用→精通路线 + CheatSheet | 知道下一步该学什么 |

### 触发方式
```
对比 owner1/repo1 vs owner2/repo2 vs owner3/repo3
compare A/B and C/D
横向对比：vuejs/core reactjs/react
```

### 输出
- 🌐 对比型 HTML 报告（5 模块锚点导航）
- 🃏 对比型信息卡片（自适应高度）
- 📦 科普素材（封面提示词 + 对比解说口播）

---

## 🎨 ui-pipeline — 三阶 UI 设计流水线

taste-skill（审美定调）→ UI UX Pro Max（设计系统）→ shadcn/ui（组件落地），支持 6 种灵活模式。

### 工作模式

| 模式 | 触发条件 | 执行阶段 |
|------|---------|---------|
| A | 美化现有页面 | 仅 taste |
| B | 只要设计规范 | 仅 uupm |
| C | 设计→代码 | 仅 shadcn |
| D | 做设计系统 | taste + uupm |
| E | 做页面（产品类型已知） | uupm + shadcn |
| F | 从零设计完整页面 | 三阶全跑 |

### 触发方式
```
"帮我设计一个注塑机管理系统的设备信息主页"
"帮我设计一套科技类小程序设计规范，包含组件"
"帮我把这个页面做得更有质感"
```

---

## 仓库结构规范

```
laobanjiu-skills/
├── README.md           ← 本文件，项目首页
├── .gitignore
├── hot-analysis/       ← GitHub 项目分析 Skill
│   ├── SKILL.md        → Agent Skill 定义
│   ├── CLAUDE.md       → AI 项目规则
│   ├── README.md       → 详细说明
│   ├── scripts/        → Python 脚本
│   └── reference/      → 分析框架参考
├── hot-compare/        ← GitHub 项目对比 Skill（新增）
│   ├── SKILL.md        → Agent Skill 定义
│   ├── CLAUDE.md       → AI 项目规则
│   ├── README.md       → 详细说明
│   └── reference/      → 对比方法论参考
├── ui-pipeline/         ← UI 三阶设计流水线（新增）
│   ├── SKILL.md        → Agent Skill 定义
│   ├── CLAUDE.md       → AI 项目规则
│   └── reference/      → taste-skill 参数手册
└── （更多 Skill 可扩展）
```

---

*由 CherryClaw 驱动 · 自用开源分享*
