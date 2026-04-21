"""
generate_jpx_zh.py
用 Claude 为 JPX 未收录的日语术语生成中文对应词，批量写入 glossary。
每批 40 个术语，输出 JSON。
"""
import json
import os
import re
import time
from pathlib import Path

import anthropic
import httpx
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent.parent
MISSING_JSON = ROOT / "glossary" / "jpx_missing.json"
GLOSSARY_MD = ROOT / "glossary" / "glossary.md"

SYSTEM = """你是一位中日金融翻译专家。
给定一批日语金融术语，请为每个术语提供对应的中文译名。

规则：
1. 只输出 JSON 数组，不输出其他内容
2. 格式：[{"ja": "日语术语", "zh": "中文对应词"}, ...]
3. 中文译名要简洁，符合中国金融行业惯例（大陆简体）
4. 若某术语极度专属日本市场、在中文金融语境中完全没有对应概念（如专属日本制度的操作性术语），zh 填 null
5. 尽量补全，不要遗漏"""


def generate_batch(client: anthropic.Anthropic, terms: list[dict]) -> list[dict]:
    ja_list = [t["ja"] for t in terms]
    prompt = "请为以下日语金融术语提供中文对应词：\n\n" + "\n".join(f"{i+1}. {ja}" for i, ja in enumerate(ja_list))

    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = msg.content[0].text.strip()
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        print(f"  [WARN] parse failed: {raw[:100]}")
        return []
    data = json.loads(match.group())
    return data


def append_to_glossary(pairs: list[dict]):
    """将 {zh, ja} 追加到 glossary.md 第十一节"""
    md = GLOSSARY_MD.read_text(encoding="utf-8")

    # 找到文件末尾，追加新节
    new_lines = []
    for p in pairs:
        if p.get("zh") and p.get("ja") and p["zh"] != "null":
            new_lines.append(f'| {p["zh"]} | {p["ja"]} | JPX | |')

    if not new_lines:
        return 0

    section_header = "\n## 十一、JPX 日本取引所グループ用語集\n\n| 中文 | 日语 | 英文/场景 | 注 |\n|------|------|-----------|----|\n"

    # 检查是否已有十一节
    if "十一、JPX" in md:
        # 追加到已有节末
        md = md.rstrip() + "\n" + "\n".join(new_lines) + "\n"
    else:
        md = md.rstrip() + section_header + "\n".join(new_lines) + "\n"

    GLOSSARY_MD.write_text(md, encoding="utf-8")
    return len(new_lines)


if __name__ == "__main__":
    client = anthropic.Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        base_url=os.getenv("ANTHROPIC_BASE_URL"),
        http_client=httpx.Client(trust_env=False),
    )

    missing = json.loads(MISSING_JSON.read_text(encoding="utf-8"))
    print(f"未收录术语总数: {len(missing)}")

    batch_size = 40
    all_pairs = []
    total_batches = (len(missing) + batch_size - 1) // batch_size

    for i in range(0, len(missing), batch_size):
        batch = missing[i : i + batch_size]
        batch_num = i // batch_size + 1
        print(f"处理批次 {batch_num}/{total_batches} ({len(batch)} terms)...", end=" ", flush=True)
        pairs = generate_batch(client, batch)
        valid = [p for p in pairs if p.get("zh") and p["zh"] != "null"]
        all_pairs.extend(valid)
        print(f"有效 {len(valid)} 条")
        time.sleep(0.5)

    print(f"\n共生成 {len(all_pairs)} 个有效中日对照")

    # 写入 glossary
    added = append_to_glossary(all_pairs)
    print(f"已追加 {added} 条到 glossary.md")

    # 也保存一份对照表
    out = ROOT / "glossary" / "jpx_zh_pairs.json"
    out.write_text(json.dumps(all_pairs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"对照表已保存到 {out}")
