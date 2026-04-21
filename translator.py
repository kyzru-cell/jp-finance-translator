"""
translator.py
调用 DeepL API 进行中文→日语翻译，使用已上传的 Glossary 强制术语。
"""

import os
from dotenv import load_dotenv
from glossary_convert import load_glossary_id

load_dotenv()


def run(text: str, glossary_id: str | None = None) -> str:
    """
    使用 DeepL 翻译文本。
    glossary_id 未传入时自动从本地配置读取。
    """
    import deepl

    api_key = os.getenv("DEEPL_API_KEY")
    if not api_key:
        raise EnvironmentError("未设置 DEEPL_API_KEY")

    translator = deepl.Translator(api_key)

    # 自动读取已上传的 glossary_id
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
