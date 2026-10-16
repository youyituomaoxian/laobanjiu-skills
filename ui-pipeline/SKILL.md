---
name: ui-pipeline
description: 三阶 UI 设计流水线——taste-skill v2 审美定调 → UI UX Pro Max 设计系统 → shadcn/ui 组件落地。支持 6 种灵活模式（仅审美/仅设计系统/仅组件/定调+设计/设计+组件/全流程），按用户需求自动路由。注意：taste-skill v2 为 dial-free 重写，且明确「不适用于 dashboard / 应用界面」——公开页走 v2 的 draw/inspector 全流程，B端/dashboard 走 v2 提炼的 craft laws 审美红线。触发词：帮我设计、设计一个、设计系统、设计规范、美化、优化页面、ui设计、界面设计、做设计。
---

# UI Pipeline — 三阶设计流水线

taste-skill v2 → UI UX Pro Max → shadcn/ui 三阶段灵活组装，按需求自动路由。

> **v2 跟随说明**：taste-skill 已从旧版的「V/D/M 三档拨盘」重写为 **dial-free** 版本。旧拨盘（VARIANCE/DENSITY/MOTION 0-10）与对应的 `taste-skill_参数手册.md` 旧内容已作废。v2 面向**公开页**（landing / 营销站 / 作品集 / 产品页 / 官网 / 宣传页），并明确声明**不适用于 dashboard / 应用界面**。本流水线阶段 1 据此分两条路径，详见下文。

---

## 触发方式

```
"帮我设计一个注塑机管理系统的设备信息主页"
"帮我设计一套科技类小程序设计规范，包含组件"
"帮我把这个页面做得更有质感"
"基于 SaaS 产品类型出一套配色方案"
"把这些设计参数转成 React 组件"
```

---

## 执行流程

### 第零步：意图解析（必执行）

从用户输入中提取以下信息，决定走 A~F 哪个模式，并判定阶段 1 走 **路径 P（公开页）** 还是 **路径 B（B端/dashboard）**：

| 提取项 | 说明 | 示例 |
|--------|------|------|
| 要什么 | 设计规范 / 完整页面 / 组件代码 / 仅调审美 | "设备信息主页" → 完整页面 |
| 产品类型 | SaaS / 工业制造 / 电商 / 医疗 / ... | "注塑机管理系统" → 工业制造 |
| 目标平台 | Web / 微信小程序 / iOS / Android / 跨平台 | "微信小程序" → Mobile/小程序 |
| 风格关键词 | 科技蓝 / 极简 / 暗色 / 玻璃质感 / ... | "科技蓝" |
| 页面类型 | **公开页**（官网/营销/作品集/产品页）还是 **B端/dashboard/应用界面** | "注塑机管理主页" → B端 |
| 是否修改已有 | 用户是否有现成代码/页面需要在此基础上改 | 无 → 从零 |

### 模式路由表

| 模式 | 触发条件 | 执行阶段 |
|------|---------|---------|
| A | 只说"美化/优化/调整"现有页面 | 仅 taste |
| B | 只要"配色/字体/设计规范" | 仅 uupm |
| C | 已有设计参数，要"转成代码/实现" | 仅 shadcn |
| D | 要做"设计系统/设计规范" | taste + uupm |
| E | 要做"XX类型产品的XX页面"，无审美要求 | uupm + shadcn |
| F | 要从零做完整页面 | taste + uupm + shadcn |

---

### 阶段 1：审美定调（跟随 taste-skill v2）

**何时执行**：模式 A / D / F

**v2 范围判定（必须先行）**：

- **路径 P — 公开页**（landing / 营销站 / 作品集 / 产品页 / 官网 / 宣传页 / 活动页）：
  完整委托给 taste-skill v2。直接按其 SKILL.md 的 1–10 步运行：读 brief → 写论点 → `draw.mjs` 抽方向 → 找 idea → 写文案 → 静态构建 → `lint.mjs`+`inspect.mjs` 门禁 → 看片 critique → 动效 → 报告。taste-skill 路径：`~/.workbuddy/skills/taste-skill/`（声明名 `design-taste-frontend`）。本流水线只负责把需求路由过去，不重复其细节。
  - 运行依赖：Node 22+（本机 `C:\Users\mask\.workbuddy\binaries\node\versions\22.22.2-6\node.exe`）+ 已装 Chrome（`C:\Program Files\Google\Chrome\Application\chrome.exe`）。`assets.mjs` 找图还需联网（无 API key）。
  - 抽方向示例：`node <taste-skill>/scripts/draw.mjs --sector <sector> --brief "<一句话>" --sections <roles> --options 3`，再 `--direction <id>` 出完整方向表。sector 列表用 `--list sectors`，roles 用 `--list roles`。

- **路径 B — B端 / dashboard / 应用界面**（弘讯工业控制 / 管理后台 / 小程序 / 应用界面）：
  **不跑** `draw.mjs` / `inspect.mjs`（v2 明确排除 dashboard）。改用 v2 提炼出的 **craft laws（工艺法则）** 作为本阶段的审美红线 / 反套路约束，注入阶段 2、3 的所有生成步骤。这些法则跨 stack 通用，对 B端同样成立：

  **排版**
  - 一页最多 5 个字号，通常 1–2 个字族；大标题与正文比 ≥ 4×。
  - 默认左对齐；整页最多一个居中时刻。
  - 正文行宽 45–75 字符；正文 16–20px，行距 1.45–1.6。

  **空间**
  - 单一网格 + 统一紧边距（16–32px），全页复用。
  - 小节之间的间距明显大于小节内部间距；相邻小节构图互不相同（B端 卡片化时尤忌千篇一律的相同卡片网格）。

  **色彩**
  - 一底 + 一墨 + 一强调；强调色只出现在动作与至多一处。
  - 正文用满墨（浅灰正文读起来像没做完）。
  - 表面靠色调微差分隔，不靠线或阴影；允许整段换底色。

  **组件**
  - 按钮扁平单色填充，要么直角要么全圆（二选一，全站固定）。
  - 导航 = 字标 + 3–5 个纯链接 + 1 个动作，无 bar 装饰。
  - 页脚/收尾是设计过的闭合，不是站点地图。

  **反 ornament 红线（一律禁止）**
  - 渐变（背景 / 按钮 / 文字）；静止物体的阴影 / 光晕。
  - 细发丝线 / 1px 描边框 / 网格线 / 十字准星。
  - 眉标（标题上方的小标签 / pill / "New·" chip）；小号大字距全大写标签。
  - 等宽字体（真实代码块除外）；序号 01/02/03 / "Step 2"。
  - 图标顶置特性卡 / 一排完全相同的卡片。
  - 玻璃拟态（backdrop-blur / 浮岛导航）；emoji / 渐变斑块 / 装饰形 / 假 dashboard 灰条。
  - 标题里的强调变色字（斜体/衬线/彩色/下划线）。

  > **用户可覆盖**：路径 B 下用户指定的品牌色 / 字族优先于上述通用红线。若品牌本身要求被禁设备（如 logo 落在渐变里、强调色为紫），保留品牌资产，并在产出报告中说明。

**向用户简述**：选了哪条路径、为什么（公开页→v2 全流程 / B端→v2 craft laws），以及注入的审美约束要点。

---

### 阶段 2：UI UX Pro Max 设计系统生成

**何时执行**：模式 B / D / E / F

**执行步骤**：

1. 将产品类型 + 风格关键词 + 阶段 1 的审美约束（路径 P 的方向表 / 路径 B 的 craft laws 解释为自然语言）拼接为搜索查询
2. 调用 uupm 搜索获取设计系统：
   ```bash
   python .claude/skills/ui-ux-pro-max/scripts/search.py "<产品类型> <风格关键词>" --design-system -p "<项目名>"
   ```
3. 若用户要的是"设计规范系统"（模式 D）→ 加 `--persist` 持久化为 MASTER.md
4. 解析输出：色板（Primary/Secondary/CTA/Bg/Text）、字体配对、推荐风格、布局模式、Anti-patterns、预交付清单
5. 向用户展示设计系统摘要（色板 + 字体 + 风格）

---

### 阶段 3：shadcn/ui 组件落地

**何时执行**：模式 C / E / F

**执行步骤**：

1. 根据目标平台选择输出格式：

| 平台 | 输出技术栈 |
|------|----------|
| Web（默认） | React + Tailwind CSS + shadcn/ui |
| 微信小程序 | Taro + Tailwind（或原生 WXML/WXSS） |
| iOS | SwiftUI |
| Android | Jetpack Compose |
| 跨平台 | React Native 或 Flutter |

2. 基于阶段 2 的设计 Token（或用户直接给的设计参数）生成组件代码
3. 若走完了阶段 2：设计 Token 转换为目标框架的主题配置
4. 输出：
   - 完整页面/组件代码
   - 组件清单
   - 主题配置文件
5. 若模式 F（全流程）：额外输出 MASTER.md（设计 Token 存档）供后续引用

---

## 输出规范

| 模式 | 输出内容 |
|------|---------|
| A | 审美调整说明（路径 P 走 v2 报告 / 路径 B 走 craft laws）+ 调整后的页面代码 |
| B | 设计系统说明（色板/字体/风格）+ MASTER.md（可选） |
| C | 目标平台组件代码 + 组件清单 |
| D | 设计规范文档 + MASTER.md + 组件示例代码 |
| E | 设计系统摘要 + 完整页面代码 + 组件清单 |
| F | 设计说明（含审美路径与约束）+ 设计系统 + 页面代码 + MASTER.md |

---

## 注意事项

- taste-skill 已升级 v2：**旧版 V/D/M 三档拨盘（0-10）已废弃**，不要再向 prompt 注入 `VARIANCE=` / `DENSITY=` / `MOTION=`。阶段 1 改走上文「路径 P / 路径 B」二选一。
- **v2 不适用于 dashboard / 应用界面**：B端 需求一律走路径 B（craft laws），不要调用 draw.mjs / inspect.mjs。
- 路径 P 的 `draw.mjs` / `inspect.mjs` / `assets.mjs` 需要 Node 22+ 与本地 Chrome；若环境缺其一，按 taste-skill SKILL.md 的「Special cases · No Chrome or Node 22」降级（只跑 lint.mjs + 自带浏览器截图 + critique）。
- uupm 的 search.py 需要 Python 3.x。若不可用，改用 Skill 内置的设计知识直接推理
- shadcn/ui 原生仅支持 Web（React/Vue）。小程序/移动端需用平台原生组件语法
- 阶段产物（审美约束 / 设计 Token / 代码）可独立保存，下次跳过前面阶段直接从中间阶段开始

## 参考

- 阶段 1 v2 适配细节与调用示例：`reference/taste-skill_参数手册.md`
- taste-skill v2 完整文档：`~/.workbuddy/skills/taste-skill/SKILL.md`
