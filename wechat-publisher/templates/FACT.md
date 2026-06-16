# FACT.md — 持久知识

> 跨会话有效的项目配置、技术决策、工作流约定。
> 首次运行 setup.py 后自动生成，请根据实际环境修改。

## 微信发布配置

| 项目 | 值 |
|------|-----|
| 槽位数 | 1 |
| 账号名 | 默认账号 |
| 发布方式 | draft（先入草稿箱） |
| 服务器 IP | **动态 IP** — 首次发布时通过 publish.py check 获取 |
| IP 白名单 | IP 变化后需手动在公众号后台加白 |
| AppID | {{WECHAT_APPID}} |

## 项目结构

```
{{PROJECT_ROOT}}/
├── .aws-article/
│   ├── config.yaml
│   └── presets/formatting/    # 排版主题
├── aws.env                    # 微信凭证（不入 git）
├── drafts/                    # 文章草稿
└── memory/FACT.md             # 本文件
```

## 可用排版主题

- **teal-pro**: 青碧主色 #0D9488，科技/开发者向（首选）
- **taste-blue**: 经典蓝增强版，过渡用
- **经典蓝**: 原版蓝底白字 h2，保守稳定
