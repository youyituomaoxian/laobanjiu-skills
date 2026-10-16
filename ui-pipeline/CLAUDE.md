# UI Pipeline — 三阶设计流水线

> AI 项目规则 — 三阶流水线：taste-skill v2 定审美 → UI UX Pro Max 出参数 → shadcn/ui 落组件

## 重要：taste-skill 已升级 v2（dial-free）

taste-skill 从旧版「V/D/M 三档拨盘（0-10）」重写为 **dial-free** 版本，旧拨盘已废弃。v2 明确**不适用于 dashboard / 应用界面**，只面向公开页（landing / 营销站 / 作品集 / 产品页 / 官网）。本流水线阶段 1 据此分两条路径：

- **路径 P（公开页）**：完整委托 taste-skill v2，跑 `draw.mjs` 抽方向 + `inspect.mjs` 真浏览器门禁 + `critique.md` 看片循环。
- **路径 B（B端 / dashboard / 应用界面）**：**不跑** draw/inspector，改用 v2 提炼的 **craft laws**（排版 / 空间 / 色彩 / 组件红线 + 禁 ornament 清单）作通用审美约束注入后续阶段。

## 核心命令

```bash
# 路径 P：用 taste-skill v2 抽设计方向（Node 22+ 与本地 Chrome）
node <taste-skill>/scripts/draw.mjs --sector <sector> --brief "<一句话>" --sections <roles> --options 3
node <taste-skill>/scripts/draw.mjs <同上参数, 去掉 --options> --direction <chosen-id>
node <taste-skill>/scripts/lint.mjs <源文件或目录>
node <taste-skill>/scripts/inspect.mjs <url 或 index.html 路径>

# 调用 UI UX Pro Max 设计系统
python .claude/skills/ui-ux-pro-max/scripts/search.py "<产品类型> <风格>" --design-system -p "<项目名>"

# 持久化设计系统（跨会话复用）
python .claude/skills/ui-ux-pro-max/scripts/search.py "<产品类型>" --design-system --persist -p "<项目名>"
```

## 架构红线

| 规则 | 说明 |
|------|------|
| **taste v2 无拨盘** | 旧 V/D/M（0-10）已废弃；公开页走 draw 方向表，B端走 craft laws，不要再注入 `VARIANCE=`/`DENSITY=`/`MOTION=` |
| **taste v2 范围** | 不适用于 dashboard / 应用界面；B端 需求一律走路径 B（craft laws） |
| **uupm 数据源** | 本地设计知识库（`search.py` 检索风格 / 色板 / 字体配对），不依赖任何网络 API |
| **shadcn 平台限制** | 原生仅支持 Web。小程序→Taro，移动端→SwiftUI/Compose/Flutter |
| **产物可存档** | 每个阶段输出独立快照，下次可从任意阶段恢复 |

## 模式路由（6 种）

| 模式 | 触发 | 执行 |
|------|------|------|
| A | 优化/美化现有页面 | taste |
| B | 只要设计规范 | uupm |
| C | 设计→代码 | shadcn |
| D | 做设计系统 | taste + uupm |
| E | 做页面（产品类型已知） | uupm + shadcn |
| F | 从零设计页面 | taste + uupm + shadcn |

> 模式 A / D / F 触发阶段 1（审美定调）。阶段 1 内部再按页面类型分路径 P / 路径 B。

## 依赖

- taste-skill v2（已安装，`~/.workbuddy/skills/taste-skill/`，声明名 `design-taste-frontend`；运行需 Node 22+ 与本地 Chrome，`assets.mjs` 找图需联网）
- ui-ux-pro-max（已安装，含 `search.py`）
- shadcn/ui（通过 MCP 调用或 AI 直接生成）
- Python 3.x（uupm `search.py` 需要）
- Node 22+ 与本地 Chrome（taste-skill v2 的 `draw.mjs` / `inspect.mjs` 需要）
