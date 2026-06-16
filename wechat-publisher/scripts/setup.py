#!/usr/bin/env python3
"""
wechat-publisher 项目初始化工具。

用法:
    python setup.py /path/to/project

功能:
    1. 创建项目目录结构（.aws-article/、drafts/、memory/ 等）
    2. 复制模板配置（config.yaml、aws.env.example、article.yaml、FACT.md）
    3. 检查 Python 依赖（PyYAML、Pillow）
    4. 生成初始 FACT.md（含项目路径和 AppID）
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = SKILL_DIR / "templates"
PRESETS_DIR = SKILL_DIR / "presets"


def check_deps():
    """检查 Python 依赖"""
    missing = []
    for mod, name in [("yaml", "PyYAML"), ("PIL", "Pillow")]:
        try:
            __import__(mod)
            print(f"  [OK] {name}")
        except ImportError:
            missing.append(name)
            print(f"  [MISS] {name}")

    if missing:
        print(f"\n  缺少依赖: {', '.join(missing)}")
        print(f"  安装: pip install {' '.join(missing)}")


def create_project_structure(project_root: Path):
    """创建项目目录结构"""
    dirs = [
        "",
        ".aws-article",
        ".aws-article/presets/formatting",
        ".aws-article/downloads",
        ".aws-article/tmp",
        "drafts",
        "memory",
    ]
    for d in dirs:
        (project_root / d).mkdir(parents=True, exist_ok=True)
        print(f"  [OK] {d}/")


def copy_templates(project_root: Path, appid: str):
    """复制模板配置"""
    # config.yaml
    config_dest = project_root / ".aws-article" / "config.yaml"
    if not config_dest.exists():
        shutil.copy2(TEMPLATES_DIR / "config.yaml", config_dest)
        print(f"  [OK] .aws-article/config.yaml（请替换 {{VALUE}} 占位符）")
    else:
        print(f"  [SKIP] .aws-article/config.yaml（已存在）")

    # .gitignore
    gitignore = project_root / ".gitignore"
    gitignore_tpl = TEMPLATES_DIR / ".gitignore"
    if not gitignore.exists() and gitignore_tpl.exists():
        shutil.copy2(gitignore_tpl, gitignore)
        print("  [OK] .gitignore")

    # aws.env.example
    env_example = project_root / "aws.env.example"
    if not env_example.exists():
        shutil.copy2(TEMPLATES_DIR / "aws.env.example", env_example)
        print("  [OK] aws.env.example（复制为 aws.env 并填入凭证）")
    else:
        print("  [SKIP] aws.env.example（已存在）")

    # article.yaml
    article_tpl = project_root / ".aws-article" / "article.yaml.template"
    if not article_tpl.exists():
        shutil.copy2(TEMPLATES_DIR / "article.yaml", article_tpl)
        print(f"  [OK] .aws-article/article.yaml.template（每篇文章单独复制使用）")

    # FACT.md
    fact_path = project_root / "memory" / "FACT.md"
    if not fact_path.exists():
        fact_content = TEMPLATES_DIR / "FACT.md"
        if fact_content.exists():
            content = fact_content.read_text(encoding="utf-8")
            content = content.replace("{{PROJECT_ROOT}}", str(project_root))
            content = content.replace("{{WECHAT_APPID}}", appid)
            fact_path.write_text(content, encoding="utf-8")
            print(f"  [OK] memory/FACT.md")
    else:
        print(f"  [SKIP] memory/FACT.md（已存在）")

    # Copy theme presets
    preset_dest = project_root / ".aws-article" / "presets" / "formatting"
    for yaml_file in PRESETS_DIR.rglob("*.yaml"):
        dest = preset_dest / yaml_file.name
        if not dest.exists():
            shutil.copy2(yaml_file, dest)
            print(f"  [OK] presets/formatting/{yaml_file.name}")

    print("\n  [!] 请手动将 aws.env.example 复制为 aws.env 并填入真实凭证")


def check_env(project_root: Path):
    """检查发布环境（代理 publish.py check）"""
    publish_script = SKILL_DIR / "scripts" / "publish.py"
    if publish_script.exists():
        print("\n  → 运行 publish.py check...")
        result = subprocess.run(
            [sys.executable, str(publish_script), "check"],
            cwd=str(project_root),
            capture_output=True, text=True,
        )
        # Print only the important lines
        for line in result.stdout.splitlines():
            if "[OK]" in line or "[ERROR]" in line or "[WARN]" in line:
                print(f"    {line.strip()}")
    else:
        print("  [WARN] publish.py 未找到，跳过环境检查")


def main():
    if len(sys.argv) < 2:
        print("用法: python setup.py /path/to/project")
        sys.exit(1)

    project_root = Path(sys.argv[1]).resolve()
    if not project_root.exists():
        project_root.mkdir(parents=True)
        print(f"创建项目目录: {project_root}")

    print(f"\n{'='*50}")
    print(f"  wechat-publisher 初始化")
    print(f"  项目: {project_root}")
    print(f"{'='*50}\n")

    # 1. Check deps
    print("[1/4] 检查依赖...")
    check_deps()

    # 2. Create structure
    print(f"\n[2/4] 创建项目结构...")
    create_project_structure(project_root)

    # 3. Copy templates
    print(f"\n[3/4] 复制配置模板...")
    appid = os.environ.get("WECHAT_1_APPID", "{{WECHAT_APPID}}")
    copy_templates(project_root, appid)

    # 4. Check environment
    print(f"\n[4/4] 检查发布环境...")
    check_env(project_root)

    print(f"\n{'='*50}")
    print(f"  初始化完成！")
    print(f"{'='*50}")
    print(f"""
下一步:
  1. 编辑 {project_root}/.aws-article/config.yaml 替换 {{VALUE}} 占位符
  2. cp aws.env.example aws.env 并填入微信凭证
  3. python {SKILL_DIR}/scripts/publish.py check     # 验证环境
  4. python {SKILL_DIR}/scripts/format.py --list-themes  # 查看主题
  5. 查看 {SKILL_DIR}/SKILL.md 了解完整工作流
""")


if __name__ == "__main__":
    main()
