# UI Pipeline — 三阶设计流水线

> AI 项目规则 — 三阶流水线：taste-skill 定审美 → UI UX Pro Max 出参数 → shadcn/ui 落组件

## 核心命令

```bash
# 生成 taste-skill 时间戳
# 格式: YYYYMMDD HH:MM:SS || taste-skill 定审美方向 | VARIANCE=X, DENSITY=X, MOTION=X

# 调用 UI UX Pro Max 设计系统
python .claude/skills/ui-ux-pro-max/scripts/search.py "<产品类型> <风格>" --design-system -p "<项目名>"

# 持久化设计系统（跨会话复用）
python .claude/skills/ui-ux-pro-max/scripts/search.py "<产品类型>" --design-system --persist -p "<项目名>"
```

## 架构红线

| 规则 | 说明 |
|------|------|
| **taste 参数范围** | 0-10 整数，5 为中立。小数/负数自动修正为就近合法值 |
| **taste 优先级** | taste 是宏观审美约束，高于微观 prompt 元素过滤 |
| **uupm 数据源** | OSS Insight API + README fetch（同 hot-analysis） |
| **shadcn 平台限制** | 原生仅支持 Web。小程序→Taro，移动端→SwiftUI/Compose/Flutter |
| **产物可存档** | 每个阶段输出独立快照，下次可从任意阶段恢复 |

## 模式路由（6 种）

| 模式 | 触发 | 执行 |
|------|------|------|
| A | 优化/美化现有页面 | taste |
| B | 只要设计规范 | uupm |
| C | 设计→代码 | shadcn |
| D | 做设计系统 | taste + uupm |
| E | 做页面（已知产品类型） | uupm + shadcn |
| F | 从零设计页面 | taste + uupm + shadcn |

## 依赖

- taste-skill（已安装）
- ui-ux-pro-max（已安装，含 search.py）
- shadcn/ui（通过 MCP 调用或 AI 直接生成）
- Python 3.x（uupm search.py 需要）
