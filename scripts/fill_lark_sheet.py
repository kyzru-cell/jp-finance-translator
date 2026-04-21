"""
fill_lark_sheet.py
读取飞书表格，将中文列翻译为日语，写回日语列。

用法：
  python fill_lark_sheet.py <sheet_url> [--style formal|marketing] [--dry-run]

示例：
  python fill_lark_sheet.py "https://futu.jp.feishu.cn/sheets/BymmsGGgQhVsrStp55mc0Cqfn4e"
  python fill_lark_sheet.py "https://..." --style marketing --dry-run
"""
import sys
import os
import json
import subprocess
import string
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv()


def run_lark(args: list[str]) -> dict:
    """调用 lark-cli，返回解析后的 JSON"""
    cmd = ["lark-cli"] + args
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(f"lark-cli 错误：{result.stderr.strip() or result.stdout.strip()}")
    return json.loads(result.stdout)


def col_index_to_letter(idx: int) -> str:
    """列索引（0-based）→ 列字母（A, B, ..., Z, AA, ...）"""
    result = ""
    idx += 1
    while idx:
        idx, rem = divmod(idx - 1, 26)
        result = string.ascii_uppercase[rem] + result
    return result


def fill_lark_sheet(url: str, style: str = "formal", dry_run: bool = False):
    import orchestrator

    print(f"读取表格：{url}")

    # Step 1: 获取表格信息（sheet_id）
    info = run_lark(["sheets", "+info", "--url", url])
    sheets = info.get("sheets", [])
    if not sheets:
        raise RuntimeError("未找到工作表")
    sheet_id = sheets[0]["sheet_id"]
    sheet_title = sheets[0].get("title", sheet_id)
    print(f"工作表：{sheet_title}（ID: {sheet_id}）")

    # Step 2: 读取全部数据
    data = run_lark(["sheets", "+read", "--url", url, "--range", sheet_id])
    values = data.get("values", [])
    if not values:
        print("表格为空，退出")
        return

    # Step 3: 找到"中"列和"日"列（表头第一行）
    header = values[0]
    zh_col = None
    ja_col = None
    for idx, cell in enumerate(header):
        if str(cell).strip() == "中":
            zh_col = idx
        elif str(cell).strip() == "日":
            ja_col = idx

    if zh_col is None or ja_col is None:
        print(f"未找到"中"或"日"列，表头为：{header}")
        return

    zh_letter = col_index_to_letter(zh_col)
    ja_letter = col_index_to_letter(ja_col)
    print(f"中文列：{zh_letter}（索引{zh_col}），日语列：{ja_letter}（索引{ja_col}）")
    print()

    # Step 4: 逐行翻译
    writes = []  # [(row_1based, ja_text)]
    for row_idx, row in enumerate(values[1:], start=2):  # 从第2行开始（跳过表头）
        zh_text = row[zh_col] if zh_col < len(row) else None
        ja_existing = row[ja_col] if ja_col < len(row) else None

        if not zh_text or not str(zh_text).strip():
            continue
        if ja_existing and str(ja_existing).strip():
            print(f"  行{row_idx} 跳过（日语列已有内容）：{ja_existing}")
            continue

        zh_text = str(zh_text).strip()
        print(f"  行{row_idx} 翻译: {zh_text[:40]}", end=" ", flush=True)

        if dry_run:
            print("→ [dry-run 跳过]")
            continue

        result = orchestrator.translate(zh_text, style=style)
        print(f"→ {result.final[:40]}  [评分:{result.score}]")
        writes.append((row_idx, result.final))

    if not writes:
        print("\n无需写入（所有行已有译文或为空）")
        return

    if dry_run:
        print(f"\n[dry-run] 将写入 {len(writes)} 个单元格到 {ja_letter} 列")
        return

    # Step 5: 逐行写回日语列（单元格写入）
    print(f"\n写入 {len(writes)} 条译文到飞书表格...")
    for row_1based, ja_text in writes:
        cell_range = f"{sheet_id}!{ja_letter}{row_1based}"
        run_lark([
            "sheets", "+write",
            "--url", url,
            "--range", cell_range,
            "--values", json.dumps([[ja_text]])
        ])
    print(f"完成：已写入 {len(writes)} 条")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print("用法: python fill_lark_sheet.py <sheet_url> [--style formal|marketing] [--dry-run]")
        sys.exit(1)

    url = args[0]
    style = "formal"
    dry_run = "--dry-run" in args

    if "--style" in args:
        idx = args.index("--style")
        style = args[idx + 1]

    fill_lark_sheet(url, style=style, dry_run=dry_run)
