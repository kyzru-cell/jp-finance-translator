"""
install.py — 中日金融专业翻译 Skill 一键安装脚本

用法：
  python install.py
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

# ── 颜色输出 ─────────────────────────────────────────────────
def ok(msg):   print(f"  \033[32m✓\033[0m  {msg}")
def info(msg): print(f"  \033[36m▶\033[0m  {msg}")
def warn(msg): print(f"  \033[33m!\033[0m  {msg}")
def err(msg):  print(f"  \033[31m✗\033[0m  {msg}")
def hr():      print("  " + "─" * 50)

# ── 路径 ──────────────────────────────────────────────────────
PROJECT_DIR  = Path(__file__).parent.resolve()
SKILL_SRC    = PROJECT_DIR / "skill_template" / "SKILL.md"
SKILL_DST    = Path.home() / ".claude" / "skills" / "lark-cn2jp-finance"
ENV_FILE     = PROJECT_DIR / ".env"
ENV_TEMPLATE = PROJECT_DIR / ".env.example"

print()
print("  ┌─────────────────────────────────────────────┐")
print("  │   中日金融专业翻译 Skill 安装程序 v2.0      │")
print("  └─────────────────────────────────────────────┘")
print()

# ── Step 1: 检查 Python 版本 ──────────────────────────────────
info("检查 Python 版本...")
if sys.version_info < (3, 10):
    err(f"需要 Python 3.10+，当前版本：{sys.version}")
    sys.exit(1)
ok(f"Python {sys.version.split()[0]}")
hr()

# ── Step 2: 安装 Python 依赖 ──────────────────────────────────
info("安装 Python 依赖包...")
result = subprocess.run(
    [sys.executable, "-m", "pip", "install", "-r", str(PROJECT_DIR / "requirements.txt"), "-q"],
    capture_output=True, text=True
)
if result.returncode != 0:
    err("依赖安装失败：")
    print(result.stderr)
    sys.exit(1)
ok("依赖包安装完成")
hr()

# ── Step 3: 配置 .env ─────────────────────────────────────────
info("检查 API 配置...")
if ENV_FILE.exists():
    ok(".env 文件已存在，跳过")
else:
    env_content = f"""# 中日金融专业翻译 — API 配置
# 填写后保存，不要提交到 Git

# DeepL API Key（在 deepl.com/pro-api 获取）
DEEPL_API_KEY=

# Anthropic API Key（企业内网用户填写 user-key-* 格式）
ANTHROPIC_API_KEY=

# Anthropic 代理地址（企业内网用户填写，外网用户删除此行）
ANTHROPIC_BASE_URL=https://llm-proxy.futuoa.com/aws
"""
    ENV_FILE.write_text(env_content, encoding="utf-8")
    warn(".env 文件已创建，请填写 API Key 后继续")
    print()
    print(f"    文件位置：{ENV_FILE}")
    print()
    input("    填写完成后按回车继续...")

# 检查 Key 是否已填写
env_text = ENV_FILE.read_text(encoding="utf-8")
missing = []
if "DEEPL_API_KEY=" in env_text and not any(
    line.startswith("DEEPL_API_KEY=") and len(line.split("=", 1)[1].strip()) > 0
    for line in env_text.splitlines()
):
    missing.append("DEEPL_API_KEY")
if "ANTHROPIC_API_KEY=" in env_text and not any(
    line.startswith("ANTHROPIC_API_KEY=") and len(line.split("=", 1)[1].strip()) > 0
    for line in env_text.splitlines()
):
    missing.append("ANTHROPIC_API_KEY")

if missing:
    warn(f"以下 Key 尚未填写：{', '.join(missing)}")
    warn("安装继续，但翻译功能在填写 Key 前无法使用")
else:
    ok("API Key 配置完成")
hr()

# ── Step 4: 安装 Skill 文件 ───────────────────────────────────
info("安装 Claude Code Skill...")

SKILL_DST.mkdir(parents=True, exist_ok=True)

# 读取 SKILL.md 模板，替换路径占位符
skill_template_path = PROJECT_DIR / "skill_template" / "SKILL.md"
readme_template_path = PROJECT_DIR / "skill_template" / "README.md"

project_path_str = str(PROJECT_DIR).replace("\\", "/")
home_path_str = str(Path.home()).replace("\\", "/")

for src, dst_name in [(skill_template_path, "SKILL.md"), (readme_template_path, "README.md")]:
    if not src.exists():
        warn(f"模板文件不存在：{src}，跳过")
        continue
    content = src.read_text(encoding="utf-8")
    # 替换占位符
    content = content.replace("{{PROJECT_DIR}}", project_path_str)
    content = content.replace("{{HOME_DIR}}", home_path_str)
    (SKILL_DST / dst_name).write_text(content, encoding="utf-8")

ok(f"Skill 已安装到：{SKILL_DST}")
hr()

# ── Step 5: 同步术语表到 DeepL ────────────────────────────────
info("同步术语表到 DeepL Glossary...")

# 检查 .env 里 DEEPL_API_KEY 是否有值
deepl_key_filled = any(
    line.startswith("DEEPL_API_KEY=") and len(line.split("=", 1)[1].strip()) > 0
    for line in env_text.splitlines()
)

if not deepl_key_filled:
    warn("DEEPL_API_KEY 未填写，跳过术语表同步（填写后手动执行）：")
    print(f"    python -X utf8 main.py glossary sync")
else:
    result = subprocess.run(
        [sys.executable, "-X", "utf8", str(PROJECT_DIR / "main.py"), "glossary", "sync"],
        cwd=str(PROJECT_DIR), capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode == 0:
        ok("术语表同步成功")
    else:
        warn("术语表同步失败，请手动执行：python -X utf8 main.py glossary sync")
        if result.stderr:
            print(f"    {result.stderr[:200]}")
hr()

# ── 完成 ──────────────────────────────────────────────────────
print()
print("  \033[32m安装完成！\033[0m")
print()
print("  快速验证（重启 Claude Code 后）：")
print(f"    cd {project_path_str}")
print( "    python -X utf8 main.py translate \"净利润同比增长15%\" --verbose")
print()
print("  Claude Code 使用方式：")
print("    直接说「翻译这段话：……」即可触发")
print()
print("  说明文档：")
print(f"    {SKILL_DST / 'README.md'}")
print()
