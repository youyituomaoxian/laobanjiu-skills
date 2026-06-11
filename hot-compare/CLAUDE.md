# Hot Compare — 项目横向对比工作流

> AI 项目规则 — 放入项目根目录后，AI Agent 自动读取。

## 快速开始

```bash
# 单项目深解（复用 hot-analysis 基础设施）
python scripts/fetch_repo_info.py owner/repo

# 对比分析入口 —— AI 驱动，无需专门脚本
# 用户说 "对比 A vs B" → AI 自动执行全流程
```

## 架构红线

| 规则 | 说明 |
|------|------|
| **数据源** | OSS Insight API + GitHub README fetch（同 hot-analysis） |
| **❌ 禁止编造** | 所有功能/用法以 README 为准，无文档处标注"暂无可靠信息" |
| **对比对象** | 2-5 个，超过 5 个建议分批 |
| **输出** | `output/compare_*_YYYYMMDD_HHMM.html` + 卡片 + 素材 |
| **方法论** | 严格按 `reference/对比方法论_优化版.md` 5 模块结构 |

## 5 模块结构

| 模块 | 核心内容 | 定位 |
|------|---------|------|
| ① 单项深解 | 每项目 7 项分析（+上手路径） | 了解每个项目 |
| ② 矩阵对比 | 10 行表格 + 决策指引 | 快速选型 |
| ③ 场景对抗 | 3 个场景下的实战对比 | 学会使用 |
| ④ 组合串联 | 原生组合 + 非兼容串联方案 | 成为高阶玩家 |
| ⑤ 高手路径 | 入门→会用→精通路线 + CheatSheet | 持续成长 |

## 与 hot-analysis 的关系

| 维度 | hot-analysis | hot-compare |
|------|-------------|-------------|
| 输入 | 1 个项目 | 2-5 个项目 |
| 分析框架 | 5 块（是什么/上手/任务/对比/暗坑） | 5 模块（深解/矩阵/场景/串联/路径） |
| 输出 | 长页面 + 5 卡片 | 对比型 HTML + 对比型卡片 + 素材 |
| 数据获取 | fetch_repo_info.py × 1 | fetch_repo_info.py × N |
| README | web_fetch × 1 | web_fetch × N（并发） |

## 依赖

- `scripts/fetch_repo_info.py` — 单项目元数据获取（复用）
- `scripts/generate_material.py` — 素材目录创建（复用）
- OSS Insight API + GitHub README fetch
- Python 标准库
