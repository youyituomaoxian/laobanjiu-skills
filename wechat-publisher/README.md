# wechat-publisher — 公众号发布一条龙

将 Markdown 文章排版为微信公众号格式并推送到草稿箱的 AI Agent Skill。自包含 format.py / publish.py 核心引擎，一次 clone 即可使用。

## 功能

- **写稿**：支持 khazix-writer 深度分析文风
- **配图**：封面图生成 + 正文配图上传（自动压缩）
- **审稿**：敏感词/标题/字数/结构逐项检查
- **排版**：多主题切换（teal-pro / taste-blue / 经典蓝），全部 inline CSS
- **发布**：上传封面 + 配图 → 创建草稿箱（draft 模式）

## 快速开始

```bash
# 1. 创建项目目录
mkdir my-wechat-project && cd my-wechat-project

# 2. 初始化（自动创建目录结构和模板配置）
python path/to/wechat-publisher/scripts/setup.py .

# 3. 配置凭证
cp aws.env.example aws.env
# 编辑 aws.env 填入 WECHAT_1_APPID 和 WECHAT_1_APPSECRET
# 编辑 .aws-article/config.yaml 替换 {{VALUE}} 占位符

# 4. 验证环境
python path/to/wechat-publisher/scripts/publish.py check

# 5. 写一篇文章开始发布
# 详情查看 SKILL.md 中的 6 阶段工作流
```

## 目录结构

```
wechat-publisher/
├── SKILL.md              # AI Agent 技能定义（核心）
├── skill.json            # 技能元数据
├── README.md             # 本文件
├── CLAUDE.md             # AI 项目规则
├── scripts/
│   ├── format.py         # Markdown → 微信 HTML（主题化排版）
│   ├── publish.py        # 微信 API 发布引擎
│   ├── article_init.py   # 文章元数据初始化
│   ├── getdraft.py       # 草稿箱读取工具
│   └── setup.py          # 项目初始化工具
├── presets/
│   └── formatting/
│       ├── teal-pro.yaml     # 青碧色科技风（推荐）
│       ├── taste-blue.yaml   # 经典蓝增强版
│       └── 经典蓝.yaml        # 原版蓝底白字
├── templates/
│   ├── config.yaml           # 配置模板
│   ├── aws.env.example       # 凭证模板
│   ├── article.yaml          # 文章元数据模板
│   └── FACT.md               # 持久知识模板
└── references/
    ├── pre-publish-checklist.md
    └── wechat-limitations.md
```

## 依赖

- Python 3.8+
- PyYAML（`pip install pyyaml`）
- Pillow（可选，用于图片压缩：`pip install pillow`）
- 微信公众号（需已开通并获取 APPID/APPSECRET）

## 排版主题

| 主题 | 风格 | 使用方式 |
|------|------|---------|
| **teal-pro** | 青碧主色，h2 底部装饰线，卡片式引用，霓虹代码块 | `--theme teal-pro` |
| taste-blue | 经典蓝增强，圆角卡片+阴影 | `--theme taste-blue` |
| 经典蓝 | 原版蓝底白字 | `--theme 经典蓝` |

自定义主题：在 `.aws-article/presets/formatting/` 下创建 YAML 文件即可。

## 微信发布配置

| 项目 | 说明 |
|------|------|
| 发布方式 | draft（先入草稿箱，不自动发布） |
| IP 白名单 | 首次发布需加白，IP 变化后需更新 |
| 图片格式 | 仅 JPG/PNG，不支持 WebP |
| 封面比例 | 900×383（2.35:1） |

## 许可证

MIT License。format.py / publish.py 基于 [aws-wechat-article-*](https://github.com/aiworkskills/wechat-article-skills)（MIT）修改，保留原始版权声明。
