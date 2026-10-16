# taste-skill 参数手册（v2 适配版）

> 旧版「V/D/M 三档拨盘（0-10）」已随 taste-skill v2 重写**彻底移除**，本文档改为记录 v2 的调用方式与审美约束映射。

## 1. v2 是什么 / 不是什么

- **是什么**：dial-free 的 anti-slop 前端审美 skill。用 `draw.mjs` 从 247 个真实获奖站提炼的库里抽设计方向（idea / composition / type / palette / photos / section blueprints），用 `inspect.mjs` 真浏览器门禁把「house rules」落到测量上，再用 `critique.md` 看片循环收尾。
- **不是什么**：**不适用于 dashboard / 应用界面**。它面向公开页（landing / 营销站 / 作品集 / 产品页 / 官网 / 宣传页）。B端 需求不要走它的 draw/inspector。

## 2. 安装位置

- 全局：`~/.workbuddy/skills/taste-skill/`（声明名 `design-taste-frontend`）。
- 运行依赖：Node 22+（本机 `C:\Users\mask\.workbuddy\binaries\node\versions\22.22.2-6\node.exe`）+ 本地 Chrome（`C:\Program Files\Google\Chrome\Application\chrome.exe`）。`assets.mjs` 找图需联网，无 API key。

## 3. 路径 P（公开页）调用示例

```bash
NODE="C:/Users/mask/.workbuddy/binaries/node/versions/22.22.2-6/node.exe"
SKILL="C:/Users/mask/.workbuddy/skills/taste-skill"

# 列出可选 sector / role
"$NODE" "$SKILL/scripts/draw.mjs" --list sectors
"$NODE" "$SKILL/scripts/draw.mjs" --list roles

# 先抽 3 个方向
"$NODE" "$SKILL/scripts/draw.mjs" --sector saas \
  --brief "注塑机厂商的海外营销官网" \
  --sections intro,features,showcase,proof,cta,footer \
  --options 3

# 选定方向后出完整方向表
"$NODE" "$SKILL/scripts/draw.mjs" --sector saas \
  --brief "注塑机厂商的海外营销官网" \
  --sections intro,features,showcase,proof,cta,footer \
  --direction <chosen-id>

# 门禁：源码 lint + 真浏览器 inspect（1440/768/390 三宽，存截图到 .taste-skill/inspect/）
"$NODE" "$SKILL/scripts/lint.mjs" <源文件或目录>
"$NODE" "$SKILL/scripts/inspect.mjs" <url 或 index.html 路径>
```

`draw.mjs` 关键参数：`--sector`、`--brief`、`--sections`、`--tone`（quiet/bold/warm/technical/playful/luxury/editorial，仅当 brief 明确要时才传）、`--have`（真实存在的资产：photography/product-photo/product-ui/illustration/video）、`--keep palette,type`（品牌已定色/字时）、`--redraw`、`--alternatives`、`--show`。

## 4. 路径 B（B端 / dashboard）审美红线速查

不走脚本，把下列「craft laws」作为通用审美约束注入后续生成：

| 维度 | 红线 / 法则 |
|------|-----------|
| 排版 | 一页 ≤5 字号，1–2 字族；大标题/正文 ≥4×；默认左对齐，最多 1 个居中；行宽 45–75 字符；正文 16–20px |
| 空间 | 单一网格 + 统一紧边距(16–32px)；小节间距 ≫ 小节内间距；相邻小节构图不同 |
| 色彩 | 一底+一墨+一强调；正文满墨（浅灰像没做完）；表面靠色调微差分隔；允许整段换底色 |
| 组件 | 按钮扁平单色，直角或全圆二选一固定；导航=字标+3–5 链接+1 动作；收尾是设计不是地图 |
| 禁 ornament | 渐变 / 静止阴影 / 发丝线 / 眉标 / 等宽(代码外) / 序号 01/02/03 / 大字距全大写小标签 / 图标顶置卡 / 玻璃拟态 / emoji / 假灰条 / 标题变色字 |

> 用户指定品牌色 / 字族优先；品牌本身要求被禁设备时保留品牌资产并在报告说明。

## 5. 旧拨盘 → v2 迁移对照

| 旧（v1/v2-experimental） | v2 替代 |
|--------------------------|---------|
| `VARIANCE=2..8` 构图方差 | 路径 P：`draw.mjs --direction` 抽真实构图；路径 B：craft laws「相邻小节构图不同」 |
| `DENSITY=3..8` 视觉密度 | 路径 P：方向表自带密度；路径 B：craft laws「小节间距 / 满内容」 |
| `MOTION=0..4` 动效强度 | 路径 P：v2 步骤 9 动效层（签名动作+入场+反馈+移动图片，inspector 数移动元素 ≥8）；路径 B：按项目既有动效规范 |
| 把 `{V,D,M}` 注入 prompt 头部 | 改为注入路径 P 的方向表 或 路径 B 的 craft laws 文本 |
