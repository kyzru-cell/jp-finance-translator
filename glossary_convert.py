"""
glossary_convert.py
将 glossary.md 中的中日词条解析并导出为 DeepL TSV 格式，同时支持上传到 DeepL。

用法：
  python glossary_convert.py export              # 导出 TSV
  python glossary_convert.py upload              # 导出并上传到 DeepL
  python glossary_convert.py list                # 列出已上传的 Glossary
  python glossary_convert.py delete <id>         # 删除指定 Glossary
"""

import re
import os
import json
import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv

load_dotenv()
app = typer.Typer()
console = Console(force_terminal=True, legacy_windows=False)

GLOSSARY_MD = Path(__file__).parent / "glossary" / "glossary.md"
GLOSSARY_TSV = Path(__file__).parent / "glossary" / "glossary_deepl.tsv"
GLOSSARY_ID_FILE = Path(__file__).parent / "glossary" / "deepl_glossary_id.json"


def parse_glossary_md(path: Path) -> dict[str, str]:
    """
    解析 glossary.md，提取所有表格中的 中文 → 日语 词对。
    跳过表头行、分隔行、注释行，以及日语列为空的行。
    """
    entries: dict[str, str] = {}
    text = path.read_text(encoding="utf-8")

    for line in text.splitlines():
        # 只处理表格内容行（以 | 开头，非表头/分隔符）
        if not line.startswith("|"):
            continue
        # 跳过分隔行 |---|---|
        if re.match(r"^\|[-| ]+\|$", line):
            continue

        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) < 2:
            continue

        zh = cols[0].strip()
        ja = cols[1].strip()

        # 跳过表头（中文、日语、读音 等字样）
        if zh in ("中文", "日语", "读音", "注", "") or ja in ("日语", "读音", ""):
            continue
        # 跳过含斜杠的复合词条（取第一个）
        if "／" in zh:
            zh = zh.split("／")[0].strip()
        if "/" in zh and len(zh) > 6:
            zh = zh.split("/")[0].strip()
        # 日语列有内容才录入
        if ja and zh:
            entries[zh] = ja

    return entries


def export_tsv(entries: dict[str, str], output: Path) -> int:
    """导出为 DeepL 要求的 TSV 格式（source\ttarget）"""
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{zh}\t{ja}" for zh, ja in entries.items()]
    output.write_text("\n".join(lines), encoding="utf-8")
    return len(lines)


@app.command()
def export(
    md_path: Optional[Path] = typer.Option(GLOSSARY_MD, help="glossary.md 路径"),
    tsv_path: Optional[Path] = typer.Option(GLOSSARY_TSV, help="输出 TSV 路径"),
):
    """解析 glossary.md，导出 DeepL TSV 文件"""
    console.print(f"[cyan]解析[/cyan] {md_path}")
    entries = parse_glossary_md(md_path)
    count = export_tsv(entries, tsv_path)
    console.print(f"[green]✓[/green] 导出 {count} 条词条 → {tsv_path}")

    # 预览前5条
    table = Table("中文", "日语", title="词条预览（前5条）")
    for zh, ja in list(entries.items())[:5]:
        table.add_row(zh, ja)
    console.print(table)


@app.command()
def upload(
    name: str = typer.Option("finance-cn2jp", help="Glossary 名称"),
    md_path: Optional[Path] = typer.Option(GLOSSARY_MD, help="glossary.md 路径"),
):
    """导出 TSV 并上传到 DeepL，保存 glossary_id"""
    api_key = os.getenv("DEEPL_API_KEY")
    if not api_key:
        console.print("[red]错误：未设置 DEEPL_API_KEY[/red]")
        raise typer.Exit(1)

    try:
        import deepl
    except ImportError:
        console.print("[red]错误：请先 pip install deepl[/red]")
        raise typer.Exit(1)

    # 解析词条
    console.print(f"[cyan]解析[/cyan] {md_path}")
    entries = parse_glossary_md(md_path)
    count = export_tsv(entries, GLOSSARY_TSV)
    console.print(f"[green]✓[/green] 解析到 {count} 条词条")

    # 上传
    translator = deepl.Translator(api_key)
    console.print(f"[cyan]上传中...[/cyan]")
    glossary = translator.create_glossary(
        name=name,
        source_lang="ZH",
        target_lang="JA",
        entries=entries,
    )

    # 保存 ID
    saved = {"glossary_id": glossary.glossary_id, "name": name, "entry_count": count}
    GLOSSARY_ID_FILE.write_text(json.dumps(saved, ensure_ascii=False, indent=2), encoding="utf-8")

    console.print(f"[green]✓ 上传成功[/green]")
    console.print(f"  Glossary ID: [bold]{glossary.glossary_id}[/bold]")
    console.print(f"  词条数量：{count}")
    console.print(f"  ID 已保存至：{GLOSSARY_ID_FILE}")


@app.command("list")
def list_glossaries():
    """列出 DeepL 账户下所有已上传的 Glossary"""
    api_key = os.getenv("DEEPL_API_KEY")
    if not api_key:
        console.print("[red]错误：未设置 DEEPL_API_KEY[/red]")
        raise typer.Exit(1)
    import deepl
    translator = deepl.Translator(api_key)
    glossaries = translator.list_glossaries()
    if not glossaries:
        console.print("暂无已上传的 Glossary")
        return
    table = Table("ID", "名称", "词条数", "创建时间")
    for g in glossaries:
        table.add_row(g.glossary_id, g.name, str(g.entry_count), str(g.creation_time))
    console.print(table)


@app.command()
def delete(glossary_id: str = typer.Argument(..., help="要删除的 Glossary ID")):
    """删除 DeepL 上的指定 Glossary"""
    api_key = os.getenv("DEEPL_API_KEY")
    if not api_key:
        console.print("[red]错误：未设置 DEEPL_API_KEY[/red]")
        raise typer.Exit(1)
    import deepl
    translator = deepl.Translator(api_key)
    translator.delete_glossary(glossary_id)
    console.print(f"[green]✓[/green] 已删除 Glossary: {glossary_id}")


def load_glossary_id() -> Optional[str]:
    """读取本地保存的 glossary_id"""
    if GLOSSARY_ID_FILE.exists():
        data = json.loads(GLOSSARY_ID_FILE.read_text(encoding="utf-8"))
        return data.get("glossary_id")
    return None


if __name__ == "__main__":
    app()
