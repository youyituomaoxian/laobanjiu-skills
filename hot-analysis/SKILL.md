---
name: hot-analysis
description: "GitHub 热门开源项目深度分析——支持两种模式：① 抓取近一周 Top 3 热门项目生成交互 HTML 报告（触发词：热门分析）；② 用户指定单个项目名称或 GitHub 链接进行深度分析（触发词：分析项目 / 分析+项目名/链接）。均参照「软件工具学习.md」分析框架，输出带交互的 HTML 报告。"
---

# GitHub 热门分析

> **⚠️ 环境变量**：以下命令中的 `$PROJECT_ROOT` 代表本 Skill 所在目录（即 `SKILL.md` 所在目录，内含 `scripts/` 子目录）。请根据实际部署路径替换，或确保执行时已 `cd` 到项目根目录。

本 Skill 支持两种分析模式：

---

## 模式一：热门分析（批量）

抓取近一周 Top 3 热门项目，自动过滤重复。

### 触发方式
用户说"热门分析"或"hot analysis"或"分析热门项目"

### 执行步骤

#### 1. 运行分析脚本
```bash
cd $PROJECT_ROOT && python scripts/github_trending_weekly.py
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
- 同意 → 执行 `hot-material` Skill
- 拒绝 → 结束

---

## 模式二：单项目分析（指定分析）

用户指定 GitHub 上的任意项目进行深度分析，生成对应的交互 HTML 报告。

### 触发方式
用户输入格式示例：
- 「分析项目 vuejs/core」
- 「分析项目 https://github.com/facebook/react」
- 「帮我分析一下 owner/repo」
- 「分析项目 owner/repo」

### 执行步骤

#### 1. 提取项目名称
从用户输入中解析 `owner/repo`：
- URL 格式：`https://github.com/owner/repo` → 提取 owner, repo
- 短格式：`owner/repo` → 直接使用

#### 2. 获取项目数据
```bash
cd $PROJECT_ROOT && python scripts/fetch_repo_info.py owner/repo
```
脚本会输出项目元数据 JSON 到 `output/` 目录。

#### 3. 读取项目数据
读取生成的 `_repo_owner_repo.json`，了解项目基本信息：
- 项目名称、Star 数、Fork 数
- 编程语言、描述

#### 4. AI 撰写深度分析
参照「软件工具学习.md」的 5 块框架，AI 为该项目撰写完整分析：
1. **这是什么** — 一句话说清 + 消灭了什么麻烦 + 最适合的 3 个场景 + 绝对不适合做的事
2. **快速上手** — 最简安装命令 + 第一个成功操作验证 + 实用技巧
3. **真实任务** — 3 个典型任务（以前怎么做 vs 用这个工具怎么做）
4. **同类对比** — 相似工具的选择建议 + 黄金搭档推荐
5. **暗坑与进阶信号** — 反人类设计 + 常见误区 + 下一步学习资源

#### 5. 生成交互 HTML 报告（单项目长页面）
AI 生成单项目交互 HTML 报告，使用 Taste-Skill + UI UX PRO MAX 双设计系统：
- 深色极简主题，支持亮色/暗色切换
- **通篇长页面连续展示** 5 块分析内容（无 Tab 切换），section 间用视觉分隔
- 顶部带锚点导航菜单或浮动侧边索引，方便跳转各块
- 统计数字、回到顶部（scroll > 600px 显示）、响应式布局
- **文件名格式**：`output/analyze_owner_repo_YYYYMMDD_HHMM.html` + 更新 `latest.html`

#### 6. 向用户汇报
- 项目名称 + Star 数 + 一句话简介
- HTML 报告文件路径

---

## 通用输出规范
- **模式一（批量分析）**：Tab 切换展示 5 块分析内容（这是什么 / 快速上手 / 真实任务 / 同类对比 / 暗坑与进阶），CSS-only radio hack
- **模式二（单项目分析）**：通篇长页面连续展示 5 块分析内容，锚点导航跳转
- 两种模式共用 Taste-Skill + UI UX PRO MAX 双设计系统
- 深色极简主题，支持亮色/暗色切换
- 统计数字滚动动画、回到顶部、响应式布局
- 分析框架参照「软件工具学习.md」5 块结构
