"""
compare_jpx.py
将 JPX 术语与现有 glossary 进行对照，找出差异。
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
GLOSSARY_MD = ROOT / "glossary" / "glossary.md"
JPX_JSON = ROOT / "glossary" / "jpx_terms.json"


def load_glossary(path: Path) -> dict:
    """返回 {zh: ja, ...} 和 {ja: zh, ...}"""
    zh_to_ja = {}
    ja_to_zh = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        if re.match(r"^\|[-| ]+\|$", line):
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) < 2:
            continue
        zh, ja = cols[0].strip(), cols[1].strip()
        if zh and ja and zh not in ("中文", "日语", "读音", "注"):
            zh_to_ja[zh] = ja
            ja_to_zh[ja] = zh
    return zh_to_ja, ja_to_zh


def normalize(s: str) -> str:
    """标准化日语术语（去括号、全角空格等）"""
    s = s.strip()
    # 去掉括号及括号内容，用于模糊匹配
    s = re.sub(r"[（(][^）)]*[）)]", "", s).strip()
    s = re.sub(r"\s+", "", s)
    return s


if __name__ == "__main__":
    zh_to_ja, ja_to_zh = load_glossary(GLOSSARY_MD)
    jpx_terms = json.loads(JPX_JSON.read_text(encoding="utf-8"))

    # 建立日语归一化集合
    ja_set = set(ja_to_zh.keys())
    ja_norm_set = {normalize(j): j for j in ja_set}

    in_glossary = []
    not_in_glossary = []

    for t in jpx_terms:
        ja = t["ja"]
        ja_norm = normalize(ja)
        if ja in ja_set or ja_norm in ja_norm_set:
            in_glossary.append(ja)
        else:
            not_in_glossary.append(t)

    print(f"JPX总术语数: {len(jpx_terms)}")
    print(f"已收录: {len(in_glossary)}")
    print(f"未收录: {len(not_in_glossary)}")
    print()

    print("=== 未收录的 JPX 术语 (前60条) ===")
    for i, t in enumerate(not_in_glossary[:60]):
        print(f"  {t['ja']}  [{t['section']}]")

    # 保存完整的未收录列表
    out = ROOT / "glossary" / "jpx_missing.json"
    out.write_text(
        json.dumps(not_in_glossary, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"\n完整未收录列表已保存到 {out}")
