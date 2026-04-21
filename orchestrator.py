"""
orchestrator.py
串联三个模块，执行完整的翻译流水线。
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

import pre_processor
import translator as deepl_translator
import post_processor
from pre_processor import _load_glossary_dict, GLOSSARY_MD

load_dotenv()


@dataclass
class TranslationResult:
    source: str
    draft: str
    final: str
    terms: list[dict] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    uncovered: list[str] = field(default_factory=list)
    score: int = 0

    def summary(self) -> str:
        lines = [
            f"质量评分：{self.score}/100",
            f"识别术语：{len(self.terms)} 个（已收录 {sum(1 for t in self.terms if t['in_glossary'])} 个）",
        ]
        if self.uncovered:
            lines.append(f"未收录词汇：{'、'.join(self.uncovered)}")
        if self.issues:
            lines.append("审校问题：")
            for issue in self.issues:
                lines.append(f"  · {issue}")
        return "\n".join(lines)


# 缓存 glossary_dict，避免重复读取文件
_glossary_cache: dict | None = None


def _get_glossary() -> dict:
    global _glossary_cache
    if _glossary_cache is None:
        _glossary_cache = _load_glossary_dict(GLOSSARY_MD)
    return _glossary_cache


def translate(text: str, glossary_id: str | None = None, style: str = "formal") -> TranslationResult:
    """执行完整翻译流水线"""
    glossary_dict = _get_glossary()

    # Step 1: 术语识别
    pre_result = pre_processor.run(text, glossary_dict=glossary_dict)
    terms = pre_result["terms"]

    # Step 2: DeepL 翻译
    draft = deepl_translator.run(text, glossary_id=glossary_id)

    # Step 3: Claude 审校
    post_result = post_processor.run(text, terms, draft, style=style)

    return TranslationResult(
        source=text,
        draft=draft,
        final=post_result.get("final", draft),
        terms=terms,
        issues=post_result.get("issues", []),
        uncovered=post_result.get("uncovered", []),
        score=post_result.get("score", 0),
    )


def translate_file(input_path: Path, output_path: Path, glossary_id: str | None = None, style: str = "formal"):
    """
    按段落翻译文本文件，输出双语对照文件。
    空行视为段落分隔符。
    """
    text = input_path.read_text(encoding="utf-8")
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    results = []
    for i, para in enumerate(paragraphs, 1):
        result = translate(para, glossary_id=glossary_id, style=style)
        results.append(result)

    # 写出双语对照
    output_lines = []
    for r in results:
        output_lines.append(f"【中文】{r.source}")
        output_lines.append(f"【日語】{r.final}")
        output_lines.append("")

    output_path.write_text("\n".join(output_lines), encoding="utf-8")
    return results
