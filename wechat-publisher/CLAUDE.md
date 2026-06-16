# wechat-publisher 项目规则

## 目录约定

- 项目根目录包含 `.aws-article/config.yaml` 和 `aws.env`
- 草稿存储在 `drafts/YYYYMMDD-slug/` 下
- 排版主题在 `.aws-article/presets/formatting/` 下
- 脚本通过 `python scripts/<name>.py` 调用

## 关键路径

- format.py：`python scripts/format.py <input.md> --theme <主题> -o <output.html>`
- publish.py check：`python scripts/publish.py check`
- publish.py full：`python scripts/publish.py --account 1 full <draft-dir>`
- setup.py：`python scripts/setup.py <project-root>`

## 发布规则

- 推送到草稿箱后记录 media_id 到 article.yaml
- 不自动发布只有告知用户到后台操作
- IP 变化时更新 memory/FACT.md
