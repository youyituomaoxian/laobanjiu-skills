# Hot Compare — GitHub 项目横向对比 Skill

> 一条指令，对比 2-5 个 GitHub 项目，一步到位输出 HTML 报告 + 海报卡片 PNG + 科普素材。

---

## 什么是 Hot Compare？

基于优化版 5 模块对比方法论，让 AI 为任意 GitHub 项目组合生成专业级横向对比分析。从「了解差异」到「学会使用」到「学会组合」——一次看完，成为高阶玩家。

### 5 模块结构

| 模块 | 做什么 | 让你获得什么 |
|------|--------|------------|
| ① 单项深解 | 每个项目 7 项深入分析 | 彻底了解每个项目 |
| ② 矩阵对比 | 10 行标准表格 + 决策指引 | 快速做出选型决定 |
| ③ 场景对抗 | 3 个真实场景下的操作对比 | 学会实际使用 |
| ④ 组合串联 | 原生组合 + 非兼容串联方案 | 学会多工具联动 |
| ⑤ 高手路径 | 入门→会用→精通路线 + CheatSheet | 知道下一步该学什么 |

---

## 触发方式

```
对比 owner1/repo1 vs owner2/repo2 vs owner3/repo3
compare A/B and C/D
横向对比：vuejs/core reactjs/react angular/angular
```

---

## 输出

- 🌐 **对比型 HTML 报告**（深色极简，锚点导航，对比表格，折叠面板）
- 🃏 **海报卡片 PNG**（固定 1080×810 4:3 画布，6 张，2160×1620px @2x，导出到 `output/posters/`）
- 📦 **科普素材**（生图提示词 + 口播文案）

---

## 快速开始

```bash
git clone https://github.com/youyituomaoxian/laobanjiu-skills.git
cd laobanjiu-skills/hot-compare

# 1. 逐个拉取对比对象的元数据（每个项目跑一次）
python scripts/fetch_repo_info.py owner1/repo1
python scripts/fetch_repo_info.py owner2/repo2

# 2. 对 Agent 说「对比 owner1/repo1 vs owner2/repo2」→ AI 执行 5 模块分析，
#    输出长页 HTML + 卡片 HTML

# 3. 卡片 HTML 生成后导出 PNG（输出到 output/posters/）
python scripts/export_posters.py output/compare_A_vs_B_卡片_YYYYMMDD_HHMM.html

# 4. 汇总素材目录（AI 随后写入提示词与口播稿）
python scripts/generate_material.py
```

> 依赖：Python 3.10+（脚本用了 `X | None` 注解）、Python 标准库；海报导出另需
> `pip install playwright && playwright install chromium`。

---

## 目录结构

```
hot-compare/
├── SKILL.md                          ← Skill 定义
├── CLAUDE.md                         ← AI 项目规则
├── README.md                         ← 本文件
├── .gitignore                        ← 忽略 output/ 产物
├── scripts/
│   ├── fetch_repo_info.py             ← 单项目元数据获取（OSS Insight API）
│   ├── generate_material.py           ← 素材目录创建 + 产出汇总
│   └── export_posters.py              ← 海报卡片 PNG 导出（posters/ @2x）
├── reference/
│   └── 对比方法论_优化版.md            ← 5 模块对比框架
└── output/                            ← 运行时产物（报告 / 卡片 / posters / 素材包）
```

---

## 与 hot-analysis 的关系

| 维度 | hot-analysis | hot-compare |
|------|-------------|-------------|
| 输入 | 1 个项目 | 2-5 个项目 |
| 分析框架 | 5 块 | 5 模块 |
| 输出 | HTML + 卡片 + 素材 | HTML + 卡片 + 素材 |
| 基础设施 | 自带 `scripts/` | **自带独立 `scripts/`**（副本，互不依赖） |

> 两个目录各自持有完整的 `scripts/`，可单独 clone 使用；改动一个不影响另一个。
