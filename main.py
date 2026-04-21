"""
main.py — CLI 入口

用法：
  python main.py translate "公司净利润同比增长15%"
  python main.py translate-file report.txt --output report_ja.txt
  python main.py glossary export
  python main.py glossary upload
  python main.py glossary list
"""

import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

app = typer.Typer(help="中日金融专业翻译工具")
glossary_app = typer.Typer(help="Glossary 管理")
app.add_typer(glossary_app, name="glossary")

console = Console()


@app.command()
def translate(
    text: str = typer.Argument(..., help="要翻译的中文文本"),
    glossary_id: Optional[str] = typer.Option(None, "--glossary-id", "-g", help="DeepL Glossary ID"),
    style: str = typer.Option("formal", "--style", "-s", help="语体风格：formal（正式产品文案）或 marketing（营销推广）"),
    show_draft: bool = typer.Option(False, "--show-draft", help="同时显示 DeepL 初稿"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示详细信息"),
):
    """翻译单段中文文本"""
    from dotenv import load_dotenv
    load_dotenv()

    style_label = "[dim]营销体[/dim]" if style == "marketing" else "[dim]正式体[/dim]"
    console.print(f"[cyan]▶ 开始翻译...[/cyan] {style_label}")

    import orchestrator
    result = orchestrator.translate(text, glossary_id=glossary_id, style=style)

    # 输出结果
    console.print(Panel(result.source, title="[bold]原文[/bold]", border_style="blue"))

    if show_draft:
        console.print(Panel(result.draft, title="[dim]DeepL 初稿[/dim]", border_style="dim"))

    score_color = "green" if result.score >= 80 else "yellow" if result.score >= 60 else "red"
    console.print(Panel(
        result.final,
        title=f"[bold green]译文[/bold green]  [dim]质量评分：[/dim][{score_color}]{result.score}/100[/{score_color}]",
        border_style="green",
    ))

    if verbose:
        # 术语表
        if result.terms:
            table = Table("中文", "日语", "收录", box=box.SIMPLE)
            for t in result.terms:
                status = "[green]✓[/green]" if t["in_glossary"] else "[red]✗[/red]"
                table.add_row(t["zh"], t["ja"] or "—", status)
            console.print(table)

        # 问题列表
        if result.issues:
            console.print("[yellow]审校问题：[/yellow]")
            for issue in result.issues:
                console.print(f"  · {issue}")

        if result.uncovered:
            console.print(f"[yellow]未收录词汇：[/yellow]{', '.join(result.uncovered)}")


@app.command("translate-file")
def translate_file(
    input_file: Path = typer.Argument(..., help="输入文件路径（.txt）"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="输出文件路径"),
    glossary_id: Optional[str] = typer.Option(None, "--glossary-id", "-g"),
    style: str = typer.Option("formal", "--style", "-s", help="语体风格：formal 或 marketing"),
):
    """翻译文本文件，输出双语对照"""
    from dotenv import load_dotenv
    load_dotenv()

    if not input_file.exists():
        console.print(f"[red]文件不存在：{input_file}[/red]")
        raise typer.Exit(1)

    if output is None:
        output = input_file.with_stem(input_file.stem + "_ja")

    console.print(f"[cyan]翻译文件：[/cyan]{input_file}")

    import orchestrator
    results = orchestrator.translate_file(input_file, output, glossary_id=glossary_id, style=style)

    avg_score = sum(r.score for r in results) // len(results) if results else 0
    console.print(f"[green]✓ 完成[/green] {len(results)} 段，平均质量 {avg_score}/100")
    console.print(f"  输出文件：{output}")


@app.command("translate-doc")
def translate_doc(
    input_file: Path = typer.Argument(..., help="输入文件路径（.docx 或 .pdf）"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="输出 .docx 路径"),
    glossary_id: Optional[str] = typer.Option(None, "--glossary-id", "-g"),
    style: str = typer.Option("formal", "--style", "-s", help="语体风格：formal 或 marketing"),
    batch_size: int = typer.Option(5, "--batch", "-b", help="每批翻译段落数"),
):
    """翻译 Word/PDF 文档，输出双语对照 Word 文件"""
    from dotenv import load_dotenv
    load_dotenv()

    if not input_file.exists():
        console.print(f"[red]文件不存在：{input_file}[/red]")
        raise typer.Exit(1)

    suffix = input_file.suffix.lower()
    if suffix not in (".docx", ".pdf"):
        console.print(f"[red]不支持的格式：{suffix}，请使用 .docx 或 .pdf[/red]")
        raise typer.Exit(1)

    console.print(f"[cyan]读取文档：[/cyan]{input_file}")

    import doc_translator
    result = doc_translator.translate_doc(
        input_path=input_file,
        output_path=output,
        glossary_id=glossary_id,
        style=style,
        batch_size=batch_size,
    )

    console.print(f"\n[green]✓ 翻译完成[/green]")
    console.print(f"  段落总数：{result.total_paragraphs}（翻译 {result.translated} 段，跳过 {result.skipped} 段）")
    console.print(f"  平均质量：{result.avg_score}/100")
    console.print(f"  输出文件：[bold]{result.output_path}[/bold]")


# ── Glossary 子命令 ──────────────────────────────────────────

@glossary_app.command("export")
def glossary_export():
    """解析 glossary.md，导出 TSV"""
    from glossary_convert import app as gc_app
    from typer.testing import CliRunner
    import glossary_convert
    glossary_convert.export()


@glossary_app.command("upload")
def glossary_upload(name: str = typer.Option("finance-cn2jp", help="Glossary 名称")):
    """上传 Glossary 到 DeepL"""
    import glossary_convert
    glossary_convert.upload(name=name)


@glossary_app.command("list")
def glossary_list():
    """列出已上传的 Glossary"""
    import glossary_convert
    glossary_convert.list_glossaries()


@glossary_app.command("sync")
def glossary_sync(name: str = typer.Option("finance-cn2jp")):
    """重新解析 glossary.md 并更新 DeepL（先删旧版再上传）"""
    from dotenv import load_dotenv
    load_dotenv()

    import deepl, os, json
    from glossary_convert import load_glossary_id, GLOSSARY_ID_FILE

    api_key = os.getenv("DEEPL_API_KEY")
    if not api_key:
        console.print("[red]未设置 DEEPL_API_KEY[/red]")
        raise typer.Exit(1)

    translator = deepl.Translator(api_key)

    # 删除旧版
    old_id = load_glossary_id()
    if old_id:
        try:
            translator.delete_glossary(old_id)
            console.print(f"[dim]已删除旧 Glossary: {old_id}[/dim]")
        except Exception:
            pass

    # 重新上传
    import glossary_convert
    glossary_convert.upload(name=name, md_path=glossary_convert.GLOSSARY_MD)


if __name__ == "__main__":
    app()
