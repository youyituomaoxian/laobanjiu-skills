# GitHub 热门分析工作流

> 项目级 AI 规则 — 将本文件放入项目根目录后，AI Agent 自动读取。

## 快速开始

```bash
# 1. 运行热门分析（抓取 → 分析 → 生成交互式 HTML 报告）
python scripts/github_trending_weekly.py

# 2. 分析指定 GitHub 项目（单项目深度分析）
python scripts/fetch_repo_info.py owner/repo

# 3. 生成科普素材（基于最新一期报告，可选步骤）
python scripts/generate_material.py
```

## 架构红线

| 项目 | 说明 |
|------|------|
| **数据源** | OSS Insight API（`https://ossinsight.io/api/mcp`）— 免费，无需 Token |
| **❌ 禁用 GitHub API** | 对特定地区网络不可达，请使用 OSS Insight |
| **❌ 禁止 python3** | Windows 下 WindowsApps 版 python3 报 exit 49，请使用 `python` |
| **输出（批量）** | `output/github_hot_analysis_YYYYMMDD_HHMM.html` + `output/latest.html` |
| **输出（单项目）** | `output/analyze_owner_repo_YYYYMMDD_HHMM.html` + `output/latest.html` |
| **分析框架** | 见 `reference/软件工具学习.md`，每个项目按 5 块结构分析（这是什么 / 快速上手 / 真实任务 / 同类对比 / 暗坑与进阶） |
| **❌ Tab 结构红线**（仅批量分析） | CSS-only Tab 的 radio `<input>` 必须与面板 `<section>` 为同级兄弟（同属 `<main>`），否则 `~` 选择器失效。单项目分析为长页面，无需 Tab 结构 |

## 核心功能

### 1. 热门分析（hot-analysis）
- 手动触发 GitHub Trending 抓取（目前仅支持手动运行脚本，无自动调度机制）
- 每次选 Top 10 候选 → 去重过滤 → 最终深度分析 3 个项目
- 输出带交互的深色极简风 HTML 报告
- 内置重复项目检测机制（Star 增长 ≥30% 或 ≥500 视为重大更新，60 天过期）

### 2. 单项目分析（specified analysis）
- 用户指定项目名称或 GitHub URL，AI 深度分析后生成交互 HTML 报告
- 数据获取: `python scripts/fetch_repo_info.py owner/repo`
- 输出: `output/analyze_owner_repo_YYYYMMDD_HHMM.html` + 更新 `output/latest.html`
- 触发: 「分析项目 owner/repo」或「分析项目 https://github.com/...」

### 3. 素材生成（hot-material）
- 解析最新 HTML 报告，为每个项目生成两种素材
- 生图提示词（英文，GPT-image2 适用，9:16 竖版科普信息卡）
- 口播文案（中文，~300 字短视频脚本）

## 输出目录结构

```
output/
├── github_hot_analysis_YYYYMMDD_HHMM.html         # 批量分析报告
├── analyze_owner_repo_YYYYMMDD_HHMM.html           # 单项目分析报告
├── latest.html                                      # 最新版报告（覆盖）
├── _repo_owner_repo.json                            # 单项目元数据缓存
├── analysis_history.json                            # 重复检测历史记录
└── 素材输出_YYYYMMDD_HHMM/                          # 素材包（可选生成）
    ├── 00_本期概览.md
    ├── _projects.json
    ├── 【HTML报告】/
    ├── 【项目提示词】/
    └── 【口播文案】/
```

## 交互特性（HTML 报告）
- **批量分析**: ① CSS-only Tab 切换（radio hack）② 明暗主题切换 ③ 统计数字滚动动画 ④ 折叠全文 ⑤ 浮动回到顶部 ⑥ 平滑滚动 ⑦ 响应式 ⑧ prefers-reduced-motion
- **单项目分析**: 通篇长页面连续展示 5 块内容，顶部锚点导航菜单，无 Tab 切换

## 设计系统
- **Taste-Skill**: HSL 变量化色彩、Type Scale 1.25、4px 间距网格、卡片交错旋转 ±0.3deg、三级表面质感
- **UI UX PRO MAX**: 玻璃拟态卡片、弹性 spring 动效（cubic-bezier(0.34, 1.56, 0.64, 1)）、多层阴影体系

## 依赖
- Python 标准库（urllib.request, json, datetime, re, pathlib）
- OSS Insight API 可访问
- 网络连接正常
