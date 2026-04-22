"""
pre_processor.py
用 Claude 识别输入文本中的金融术语，并在 glossary 中查找对应译法。

输出结构：
{
  "text": "原始中文文本",
  "terms": [
    {"zh": "净利润", "ja": "当期純利益", "in_glossary": true},
    {"zh": "城投债", "ja": null, "in_glossary": false}
  ]
}
"""

import os
import json
import re
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

GLOSSARY_MD = Path(__file__).parent / "glossary" / "glossary.md"


def _load_glossary_dict(path: Path) -> dict[str, str]:
    """从 glossary.md 构建 {中文: 日语} 查询字典"""
    entries: dict[str, str] = {}
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
            entries[zh] = ja
    return entries


def run(text: str, glossary_dict: Optional[dict[str, str]] = None, source_lang: str = "zh") -> dict:
    """
    识别文本中的金融术语，返回术语表。
    source_lang: "zh"（默认，中文→日语）或 "ja"（日语→中文）
    glossary_dict 可外部传入避免重复解析。
      - source_lang="zh" 时传入 {zh: ja}
      - source_lang="ja" 时传入 {ja: zh}（反向词典）
    """
    import anthropic

    if source_lang == "ja":
        # 日语→中文：使用反向词典 {ja: zh}
        if glossary_dict is None:
            forward = _load_glossary_dict(GLOSSARY_MD)
            glossary_dict = {ja: zh for zh, ja in forward.items() if ja and zh}

        import httpx
        client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            base_url=os.getenv("ANTHROPIC_BASE_URL"),
            http_client=httpx.Client(trust_env=False),
        )

        glossary_sample = list(glossary_dict.keys())[:50]

        system_prompt = """あなたは日中金融翻訳の専門家です。タスクはひとつ：
ユーザーが提供した日本語金融テキストから、金融専門用語をすべて識別してリストアップしてください。

出力ルール：
1. JSONのみ出力。他の内容は不要
2. JSON形式：{"terms": ["用語1", "用語2", ...]}
3. 金融専門用語のみ。一般的な語（「会社」「今年」等）は除く
4. 各用語は簡潔に（重複なし）"""

        user_prompt = f"""以下の日本語テキストから金融専門用語を識別してください：

{text}

参考用語（一部）：{', '.join(glossary_sample)}"""

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        raw = message.content[0].text.strip()
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return {"text": text, "terms": []}

        data = json.loads(match.group())
        term_list = data.get("terms", [])

        terms = []
        for ja_term in term_list:
            if ja_term in glossary_dict:
                terms.append({"ja": ja_term, "zh": glossary_dict[ja_term], "in_glossary": True})
            else:
                matched = None
                for key in glossary_dict:
                    if key in ja_term or ja_term in key:
                        matched = glossary_dict[key]
                        break
                terms.append({"ja": ja_term, "zh": matched, "in_glossary": matched is not None})

        return {"text": text, "terms": terms}

    else:
        # 原来的 ZH→JA 逻辑
        if glossary_dict is None:
            glossary_dict = _load_glossary_dict(GLOSSARY_MD)

        import httpx
        client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            base_url=os.getenv("ANTHROPIC_BASE_URL"),
            http_client=httpx.Client(trust_env=False),
        )

        glossary_keys = list(glossary_dict.keys())
        glossary_sample = glossary_keys[:300]

        system_prompt = """你是一位中日金融翻译专家。你的任务只有一个：
从用户提供的中文金融文本中，识别并列出所有金融专业术语。

输出规则：
1. 只输出 JSON，不要输出任何其他内容
2. JSON 格式：{"terms": ["术语1", "术语2", ...]}
3. 只列出金融专业词汇，不要列出普通词汇（如"公司"、"今年"等）
4. 每个术语尽量精简（2-8个字），不要截断词义
5. 不要重复"""

        user_prompt = f"""请识别以下文本中的金融专业术语：

{text}

参考词汇范围（部分）：{', '.join(glossary_sample[:50])}"""

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        raw = message.content[0].text.strip()
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return {"text": text, "terms": []}

        data = json.loads(match.group())
        term_list = data.get("terms", [])

        terms = []
        for zh in term_list:
            if zh in glossary_dict:
                terms.append({"zh": zh, "ja": glossary_dict[zh], "in_glossary": True})
            else:
                matched = None
                for key in glossary_dict:
                    if key in zh or zh in key:
                        matched = glossary_dict[key]
                        break
                terms.append({"zh": zh, "ja": matched, "in_glossary": matched is not None})

        return {"text": text, "terms": terms}
