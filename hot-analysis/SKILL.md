---
name: hot-analysis
description: "GitHub 热门开源项目深度分析——支持两种模式：① 抓取近一周 Top 3 热门项目生成交互 HTML 报告（触发词：热门分析）；② 用户指定单个项目名称或 GitHub 链接进行深度分析（触发词：分析项目 / 分析+项目名/链接）。均参照「软件工具学习.md」分析框架，输出带交互的 HTML 报告。"
---

# GitHub 热门分析

> **⚠️ 路径约定**：以下命令中的 `SKILL_DIR` 代表本 Skill 所在目录（`C:\Users\mask\.workbuddy\skills\hot-analysis\`），内含 `scripts/` 子目录。执行时请替换为实际路径，或确保已 `cd` 到 Skill 根目录。

本 Skill 支持两种分析模式：

---

## 模式一：热门分析（批量）

抓取近一周 Top 3 热门项目，自动过滤重复。

### 触发方式
用户说"热门分析"或"hot analysis"或"分析热门项目"

### 执行步骤

#### 1. 运行分析脚本
```bash
cd SKILL_DIR && python scripts/github_trending_weekly.py
```

#### 2. 等待执行结果
脚本会输出：
- 正在获取的 3 个热门项目名称和 Star 数
- 生成的 HTML 文件路径

#### 3. 读取生成的报告
找到最新生成的 HTML 文件（在 output/ 目录下，文件名格式为 `github_hot_analysis_YYYYMMDD_HHMM.html` 或 `latest.html`），读取其内容。

#### 4. 向用户汇报结果
- 本期分析了哪 3 个项目（名称 + 作者 + Star 数 + 一句话简介）
- HTML 报告的文件路径
- 简要说明报告内容

#### 5. 询问是否继续生成素材
汇报完成后，询问：「是否需要为这期项目生成科普素材（生图提示词 + 口播文案）？」
- 同意 → AI 代理执行素材生成流程（创建目录结构：`python scripts/generate_material.py`，然后由 AI 写入提示词和口播文案）
- 拒绝 → 结束

---

## 模式二：单项目分析（指定分析）v2

用户指定 GitHub 上的任意项目进行深度分析，生成对应的交互 HTML 报告和自适应卡片。

### 触发方式
- 「分析项目 vuejs/core」
- 「分析项目 https://github.com/facebook/react」
- 「帮我分析一下 owner/repo」

### 执行步骤

#### 1. 提取项目名称
从用户输入中解析 `owner/repo`：
- URL 格式：`https://github.com/owner/repo` → 提取 owner, repo
- 短格式：`owner/repo` → 直接使用

#### 2. 获取元数据
```bash
cd SKILL_DIR && python scripts/fetch_repo_info.py owner/repo
```
输出 `output/_repo_owner_repo.json`（stars/forks/language/description）

#### 3. 获取项目实际内容（v2 新增）
由 AI 代理使用 WebFetch 工具获取项目 README.md（GitHub raw URL `https://raw.githubusercontent.com/owner/repo/main/README.md`），了解真实的安装方式、功能说明、API 用法。若 raw URL 不可达，改用 GitHub 页面 web_fetch。

#### 4. 询问分析侧重点（v2 新增）
向用户提问选择：
- [1] 全面深度分析（5 块均衡）
- [2] 重点：怎么用（放大快速上手和真实任务）
- [3] 重点：同类对比（放大同类对比和暗坑）
- [4] 快速概览（精简版）
- [5] 自定义

#### 5. AI 撰写深度分析
基于 README 真实内容，按 5 块框架撰写（参照「软件工具学习.md」）。

#### 6. 生成双输出（v2 新增）
- **输出 A**：HTML 长页面 → `output/analyze_owner_repo_YYYYMMDD_HHMM.html` + 更新 `latest.html`
- **输出 B**：海报级卡片 HTML → PNG
  - HTML 文件：`output/analyze_owner_repo_cards_YYYYMMDD_HHMM.html`
  - **固定画布 1080×810 (4:3)**，无响应式，禁用 `clamp()`
  - 海报字体层级：90px/72px/56px/24px/18px/14px/13px（见 hot-compare 字体表）
  - CSS 关键：`.deco{position:absolute}` `.poster>*:not(.noise):not(.deco){position:relative;z-index:3}` `.ftr{margin-top:auto}`
  - 生成 HTML 后**必须运行** `python scripts/export_posters.py <html_path>` 导出 2160×1620px PNG
  - 卡片内容与口播稿对应：卡1 封面→卡2 是什么→卡3 怎么用→卡4 对比→卡5 暗坑
- **输出文件夹**：HTML、卡片、PNG 放入 `output/项目名_时间/` 子目录

#### 7. 向用户汇报
- 项目名 + Star + 简介 + 双输出路径
- 询问是否继续生成素材

---

## 输出规范

### 长页 HTML 报告
- **模式一（批量）**：Tab 切换 5 块分析内容（CSS-only radio hack）
- **模式二（单项目 v2）**：HTML 长页面锚点导航
- 设计系统：Taste-Skill + UI UX PRO MAX
- 深色极简 · 统计动画 · 回到顶部 · 响应式 · prefers-reduced-motion

### 海报卡片（新增）
- **固定 1080×810 画布**，不使用 `clamp()`、不响应式
- 字体全部按海报尺度 px 定值（封面 90px / 身份卡 72px / 副标题 24px / 正文 18px / pills 14px）
- 颜色：十六进制直写（`#e2e8f0` / `#94a3b8` / `#64748b`），禁止 `rgba(255,255,255,.xx)`
- CSS 关键约束：`.deco{position:absolute}` `.poster>*:not(.noise):not(.deco){position:relative;z-index:3}`
- 生成后运行 `python scripts/export_posters.py` 导出 2160×1620px PNG

### 通用
- 分析框架参照「软件工具学习.md」5 块结构
- 输出文件夹规范：`output/项目名_时间/`
