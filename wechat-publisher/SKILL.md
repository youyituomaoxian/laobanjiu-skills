---
name: wechat-publisher
description: 公众号发布一条龙——全流程/单环节/恢复模式三模式路由。全流程：发公众号/发文章/一条龙。单环节：排版/格式化/美化/审稿/校对/配图/加封面/推送/发出去/换主题/直接发布/群发。查阅：查看草稿/列出草稿。风格：khazix风格写/深度分析文。恢复：接着上次/继续发。初始化：setup.py 自动创建项目结构和模板配置。首次使用自动引导。
homepage: https://github.com/youyituomaoxian/laobanjiu-skills
url: https://github.com/youyituomaoxian/laobanjiu-skills/tree/main/wechat-publisher
metadata:
  openclaw:
    requires:
      env: [WECHAT_1_APPID, WECHAT_1_APPSECRET]
      bins: [python3]
    primaryEnv: aws.env
---

# wechat-publisher — 公众号发布一条龙

> 从写稿到草稿箱，6 阶段管线一次走完。本技能自包含 format.py / publish.py 两个核心引擎 + teal-pro 等自定义排版主题，一次 git clone 即可使用。

**套件说明** · 本技能属于 [laobanjiu-skills](https://github.com/youyituomaoxian/laobanjiu-skills) 集合。排版脚本（format.py）和发布脚本（publish.py）基于 [aws-wechat-article-*](https://github.com/aiworkskills/wechat-article-skills)（MIT 协议）修改，保留原始版权声明。

## 能力披露

- **凭证**：读取 `aws.env`（WECHAT_1_APPID / WECHAT_1_APPSECRET）
- **网络**：publish.py / format.py 需访问微信 API（`api.weixin.qq.com`）
- **文件读写**：在项目目录下创建 drafts/YYYYMMDD-slug/ 结构
- **Shell**：调用 `python scripts/format.py` / `python scripts/publish.py`
- **无外部依赖**：所有脚本内置，无需 pip install（PyYAML / Pillow 除外，setup 时自动检测）

## 触发词

| 用户意图 | 触发词 | 路由 |
|---------|--------|------|
| **全流程** | 发公众号、发文章、一条龙、从写稿到发布、帮我发一篇 | 全流程 1→2→3→4→5→6 |
| **仅排版** | 排版、格式化、美化、转成公众号格式、帮我弄好看点 | 仅第 4 步，需已有 article.md |
| **仅发布** | 推送、发出去、入草稿箱、推送到公众号、上传封面 | 仅第 5+6 步，需已有 article.html |
| **仅写稿** | 写一篇关于、帮我写、以 khazix 风格写、深度分析文 | 仅第 1 步，产出 article.md 后停止 |
| **仅配图** | 加封面、配图、插入图片、做封面 | 仅第 2 步，需已有 article.md |
| **仅审稿** | 审稿、检查、校对、审一下、看看有什么问题 | 仅第 3 步，需已有 article.md |
| **恢复流程** | 接着上次那篇、继续发、上一篇还没发完 | 恢复模式：检测 article.yaml 判断从哪步继续 |
| **换主题重排** | 换个主题、换个排版风格、换排版 | 仅第 4 步（重新排 article.md） |
| **查阅草稿** | 查看草稿、列出草稿、草稿列表、我的草稿 | `getdraft.py list` 列出微信草稿箱 |
| **直接发布** | 直接发布、正式发布、群发 | 仅第 5+6 步（含 `publish` 子命令） |
| **首次使用** | 初始化、设置公众号、第一次用 | 仅第 0 步 |

> 路由规则：先判断用户意图命中的是「全流程」还是「单环节」触发词。全流程走 1→2→3→4→5→6 流水线。单环节仅执行对应步骤，完成后停在原地。代理在执行单环节时先检查该环节的「前置条件」，不满足则提示用户补全。

## 脚本目录

```
scripts/
├── format.py           # Markdown → 微信兼容 HTML（38KB）
├── publish.py          # 微信 API 发布引擎（42KB，含 check / full / publish 子命令）
├── article_init.py     # 文章元数据初始化（8KB）
├── getdraft.py         # 微信草稿箱读取工具（17KB）
└── setup.py            # 项目初始化工具（首次运行）
```

## 工作流

本技能分 6 阶段推进。代理根据触发词路由选择执行模式：

- **全流程模式**：用户触发「全流程」类触发词 → 按顺序执行 1→2→3→4→5→6
- **单环节模式**：用户触发「仅 XX」类触发词 → 仅执行对应步骤，完成后停止
- **恢复模式**：用户说「接着上次」「继续」时触发。读取 `drafts/` 下最新的 `article.yaml`，按以下规则判断从哪步继续：

| article.yaml 字段状态 | 从哪步继续 |
|---|---|
| article.md 存在 + 其他字段均缺 | 第 2 步（配图） |
| 无 `article.html` | 第 4 步（排版） |
| 有 `article.html` + 无 `media_id` | 第 5 步（发布检查） |
| `publish_completed: false` + 有 `media_id` | 第 6 步（重新推送） |
| `publish_completed: true` | 告知用户「已发布」 |

每阶段均标注了**前置条件**（单环节执行时需检查）和**产出**。

### 第 0 步：环境检查（首次使用时自动执行）

**触发条件**：用户说「初始化」「设置公众号」「第一次用」，或检测到 `.aws-article/config.yaml` 不存在时自动执行。
**前置条件**：项目根目录存在。
**产出**：项目目录结构 + 模板配置。

检测项目根目录是否有 `.aws-article/config.yaml`：

- 有 → 跳过，直接进入流程
- 无 → 自动运行 `python setup.py <项目根目录>` 初始化

初始化产出：
- `.aws-article/config.yaml`（占位符版本，需用户替换）
- `aws.env.example`（复制为 aws.env 并填入凭证）
- `memory/FACT.md`（持久知识）
- `presets/formatting/teal-pro.yaml` 等主题

**IP 白名单提醒**：每次运行 `publish.py check` 获取当前 IP，若返回 `errcode: 40164` 则提示用户到微信公众号后台加白。

### 第 1 步：写稿

**触发条件**：用户说「写一篇」「帮我写」「写稿」「以 khazix 风格写」。
**前置条件**：第 0 步已完成（`.aws-article/config.yaml` 存在）。
**输入**：用户意图 / 参考资料 / 分析资料
**产出**：`drafts/YYYYMMDD-slug/article.md`
**后续衔接**：全流程模式下自动进入第 2 步；单环节模式下停止。

流程：
1. 在 `drafts/` 下创建 `YYYYMMDD-slug/` 目录（以实际日期 + 文章主题命名）
2. 根据用户提供的素材写稿
3. 文章第一行固定格式：
   ```
   # 文章标题（h1，format.py 会跳过，填入微信后台标题栏）
   {embed:profile:{{公众号作者名}}}
   ```
4. 正文从 `h2` 起，字数控制在 `config.yaml` 的 `target_word_count` 范围（默认 3000-4000）
5. 创建 `drafts/YYYYMMDD-slug/article.yaml`，写入初始元数据：

```yaml
title: '{{文章标题}}'
author: '{{公众号作者名}}'
created: '{{YYYY-MM-DD}}'
default_format_preset: teal-pro
cover: cover.jpg
publish_method: draft
publish_completed: false
media_id: null
```

**支持写作风格**：
- **khazix-writer 风格**：用户说「用 khazix 风格写」时采用——场景化开头、三层分析结构、个人化叙述、数据锚点、风险分析、回环收束、行动号召 + 署名
- **常规风格**：按 config.yaml 的 `article_style` 写（默认「分析性」）

### 第 2 步：配图与封面

**触发条件**：用户说「加封面」「配图」「插入图片」「做封面」，或全流程模式下第 1 步完成后。
**前置条件**：`drafts/YYYYMMDD-slug/article.md` 已存在。
**输入**：文章标题 + 核心观点
**产出**：`cover.jpg`（封面）+ `imgs/`（正文配图）
**后续衔接**：全流程模式下自动进入第 3 步；单环节模式下停止。

流程：
1. 封面图：用户提供或 Pillow 生成（900×383，2.35:1 比例，品牌色 + 标题文字）。Pillow 生成参考：品牌色填充背景 + 黑色渐变叠加 + 标题文字（白色/灰色）+ 几何装饰圆。
2. 正文配图：用户提供截图，放入 `imgs/` 目录
3. 在 `article.md` 中用 Markdown 引用：`![描述](imgs/xxx.png)`
4. 注意：WebP 格式必须转为 JPG/PNG（微信不支持 WebP）

### 第 3 步：审稿

**触发条件**：用户说「审稿」「检查」「校对」「审一下」「看看有什么问题」，或全流程模式下第 2 步完成后。
**前置条件**：`drafts/YYYYMMDD-slug/article.md` 已存在。
**输入**：`article.md`、`article.yaml`
**产出**：审稿结果（✅/🟡/🔴）
**后续衔接**：🔴 项修改后自动重审；全流程模式下全部 ✅ 后进入第 4 步；单环节模式下停止。

按以下清单逐项检查：

| 维度 | 检查项 |
|------|--------|
| 标题 | 字数 ≤ `title_max_length`（20）、不含禁用词（炸裂/震惊/出大事了）、有吸引力 |
| 摘要 | 字数 ≤ `summary_length`（120）、概括核心、非正文首段复制 |
| 正文 | 敏感词、错别字、事实出处、原创标注 |
| 结构 | 小标题密度（每节必有）、结尾有行动号召 |

🔴 项必须修改 → 修改后重审 → 直到无 🔴 → 用户确认

### 第 4 步：排版

**触发条件**：用户说「排版」「格式化」「美化」「转成公众号格式」「弄好看点」，或全流程模式下第 3 步完成后。
**前置条件**：`drafts/YYYYMMDD-slug/article.md` 已存在。
**输入**：`article.md`、主题选择
**产出**：`article.html`（微信后台可粘贴 HTML）
**后续衔接**：全流程模式下自动进入第 5 步；单环节模式下停止。

```bash
python scripts/format.py drafts/YYYYMMDD-slug/article.md \
  --theme teal-pro \
  -o drafts/YYYYMMDD-slug/article.html
```

**可用主题**：

| 主题 | 风格 |
|------|------|
| teal-pro | 青碧主色 #0D9488，h2 底部装饰线，卡片式引用，霓虹代码块（**推荐**） |
| taste-blue | 经典蓝增强版，圆角卡片 + 阴影 |
| 经典蓝 | 原版蓝底白字 h2 |

**format.py 规则**：
- 跳过第一个 `h1`（微信后台填标题），正文从 `h2` 起
- `{embed:profile:XXX}` → 公众号名片
- `![alt](imgs/xxx.png)` → 微信兼容图片标签
- 代码块 → 深色背景霓虹字体
- 所有样式转为 inline CSS

### 第 5 步：发布检查

**触发条件**：用户说「检查发布环境」「验证」「check」，或全流程模式下第 4 步完成后。
**前置条件**：`aws.env` 已创建且包含有效凭证。
**后续衔接**：全流程模式下通过后自动进入第 6 步；单环节模式下停止。

```bash
python scripts/publish.py check
```

检查：
- `aws.env` 凭证文件是否存在
- APPID / SECRET 是否完整
- 微信 API 连通性（IP 白名单）

**若 `errcode: 40164`**：告知用户当前 IP，引导至公众号后台加白后重试。

### 第 6 步：推送到草稿箱

**触发条件**：用户说「推送」「发布」「发出去」「入草稿箱」，或全流程模式下第 5 步完成后。
**前置条件**：第 5 步发布检查通过 + 第 4 步已产出 `article.html`。
**后续衔接**：推送成功后记录 media_id，流程结束。

```bash
python scripts/publish.py --account 1 full drafts/YYYYMMDD-slug
```

自动完成：
1. 上传封面图到微信素材库
2. 上传正文配图（超 1024KB 自动压缩）
3. 创建草稿（draft 模式，不入已发布列表）

**成功后**：
- 记录 `media_id` 到 `article.yaml`
- 设置 `publish_completed: true`
- 告知用户到公众号后台→草稿箱预览发布

**直接群发（替代 draft 模式）**：当用户说「直接发布」「正式发布」「群发」时，创建草稿后追加执行：
```bash
python scripts/publish.py publish <media_id>
```
⚠️ 直接群发前须向用户确认——群发后不可撤回。

### 第 7 步：查阅草稿箱（可选）

**触发条件**：用户说「查看草稿」「列出草稿」「我的草稿」。
**前置条件**：aws.env 已配置。

```bash
python scripts/getdraft.py list
```
列出当前公众号所有草稿（media_id + 标题 + 更新时间）。也可用 `getdraft.py get <media_id>` 查看单个草稿的完整内容。

## 产出一览

| 环节 | 产出 | 存放位置 |
|------|------|---------|
| 写稿 | article.md | drafts/YYYYMMDD-slug/ |
| 封面 | cover.jpg | drafts/YYYYMMDD-slug/ |
| 配图 | xxx.png | drafts/YYYYMMDD-slug/imgs/ |
| 排版 | article.html | drafts/YYYYMMDD-slug/ |
| 元数据 | article.yaml | drafts/YYYYMMDD-slug/ |
| 草稿 | media_id | article.yaml 记录 |

## 快速开始

```bash
# 1. 创建项目目录并初始化
mkdir my-wechat-project && cd my-wechat-project
python path/to/wechat-publisher/scripts/setup.py .

# 2. 配置凭证
#    - 编辑 .aws-article/config.yaml 替换 {{VALUE}} 占位符
#    - cp aws.env.example aws.env 并填入微信凭证

# 3. 验证环境
python path/to/wechat-publisher/scripts/publish.py check

# 4. 查看可用主题
python path/to/wechat-publisher/scripts/format.py --list-themes

# 5. 写稿 → 排版 → 发布（由 Agent 根据 SKILL.md 引导完成）
```

## 安全提示

项目目录必须包含 `.gitignore`，防止凭证漏出。首次初始化时建议创建：

```gitignore
# wechat-publisher .gitignore
aws.env
.aws-article/config.yaml
```

## 常见问题

**Q: IP 不在白名单？**
A: `publish.py check` 会返回 errcode 40164 和当前 IP。登录微信公众号后台 → 设置与开发 → 安全中心 → IP 白名单，添加该 IP 后重试。

**Q: 图片上传失败？**
A: 确保图片为 JPG/PNG 格式（不支持 WebP）。单图超过 1024KB 会自动压缩。

**Q: 排版效果不对？**
A: 微信后台仅支持 inline CSS，不支持 CSS 变量、flexbox、grid、伪元素。建议在微信后台预览，不满意调整主题或使用 `--color` 覆盖主色。

**Q: 如何添加自定义主题？**
A: 在 `.aws-article/presets/formatting/` 下创建 `<主题名>.yaml`，参考 teal-pro.yaml 格式，然后 `format.py --theme <主题名>` 使用。
