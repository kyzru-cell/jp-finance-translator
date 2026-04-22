"""
translator.py
调用 DeepL API 进行翻译，支持 ZH→JA（默认）和 JA→ZH 两个方向。
使用已上传的 Glossary 强制术语。
"""

import os
from dotenv import load_dotenv
from glossary_convert import load_glossary_id, load_reversed_glossary_id

load_dotenv()


def run(text: str, glossary_id: str | None = None, direction: str = "zh2ja") -> str:
    """
    使用 DeepL 翻译文本。
    direction: "zh2ja"（中文→日语，默认）或 "ja2zh"（日语→中文）
    glossary_id 未传入时自动从本地配置读取。
    """
    import deepl

    api_key = os.getenv("DEEPL_API_KEY")
    if not api_key:
        raise EnvironmentError("未设置 DEEPL_API_KEY")

    translator = deepl.Translator(api_key)

    if direction == "ja2zh":
        if glossary_id is None:
            glossary_id = load_reversed_glossary_id()
        kwargs = {
            "source_lang": "JA",
            "target_lang": "ZH",
        }
    else:
        if glossary_id is None:
            glossary_id = load_glossary_id()
        kwargs = {
            "source_lang": "ZH",
            "target_lang": "JA",
            "formality": "more",  # 正式文体（書き言葉）
        }

    if glossary_id:
        kwargs["glossary"] = glossary_id

    result = translator.translate_text(text, **kwargs)
    return result.text


def is_available() -> bool:
    """检查 DeepL API 是否可用"""
    try:
        import deepl
        api_key = os.getenv("DEEPL_API_KEY")
        if not api_key:
            return False
        translator = deepl.Translator(api_key)
        usage = translator.get_usage()
        return usage.character.count < usage.character.limit
    except Exception:
        return False
