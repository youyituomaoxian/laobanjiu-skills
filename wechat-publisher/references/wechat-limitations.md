# 微信 CSS 限制速查

微信后台（公众号编辑器）仅支持 **inline CSS**，以下特性**不适用**：

## ❌ 不支持的 CSS 特性

| 特性 | 原因 |
|------|------|
| `display: flex` / `display: grid` | 微信渲染引擎不支持 |
| CSS 自定义属性（`--var`） | 不支持变量解析 |
| `@media` 查询 | 不支持响应式 |
| `::before` / `::after` 伪元素 | 不支持 |
| `backdrop-filter` | 不支持毛玻璃效果 |
| `animation` / `transition` | 不支持动效 |
| `position: fixed` / `sticky` | 不支持固定定位 |
| `background-clip: text` | 不支持文字渐变 |
| 外部 `<link>` 样式表 | 不加载外部资源 |
| `<script>` / JavaScript | 不支持任何 JS |

## ✅ 支持的 CSS 属性（通过 inline style）

| 类别 | 支持的属性 |
|------|-----------|
| 文本 | `color`, `font-size`, `font-weight`, `line-height`, `text-align`, `letter-spacing` |
| 背景 | `background`, `background-color`（仅单色和渐变色） |
| 盒子 | `margin`, `padding`, `border`, `border-radius`, `box-shadow` |
| 布局 | `display: block/inline/inline-block/none` |
| 尺寸 | `width`, `height`, `max-width` |

## 关键约束

1. **没有 CSS 变量** → 主题 YAML 在 format.py 编译时展开为静态值
2. **没有 flex/grid** → 布局用 `display: inline-block` + `width` 模拟
3. **没有伪元素** → 装饰效果用 `border` / `background` 实现
4. **没有 JS** → 所有交互在微信端不可用
5. **没有网络字体** → 使用系统字体栈

## 双轨输出策略

由于微信的 CSS 限制，同一篇文章可采用双轨输出：

- **微信版**：`format.py --theme teal-pro` → inline CSS HTML，发布到公众号
- **网页版**：独立 HTML，使用完整 CSS（Flex/Grid/变量/动效），适合博客/官网

两版共享同一份 `article.md` 内容源，仅渲染层不同。
