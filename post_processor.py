"""
post_processor.py
用 Claude 对 DeepL 初稿进行质量审校：
- 核查金融术语是否被正确使用
- 检查语体一致性
- 标注未收录词汇
- 输出最终译文 + 质量报告
"""

import os
import json
import re
from dotenv import load_dotenv

load_dotenv()


def run(source_text: str, terms: list[dict], draft: str, style: str = "formal") -> dict:
    """
    审校翻译结果。

    参数：
      source_text: 中文原文
      terms: pre_processor 输出的术语列表
      draft: DeepL 初稿日语译文
      style: "formal"（正式产品文案，参考SBI风格）或 "marketing"（营销推广，参考乐天风格）

    返回：
      {
        "final": "最终日语译文",
        "issues": ["问题1", ...],   # 术语错误、语体问题等
        "uncovered": ["城投债", ...],  # glossary 未收录词汇
        "score": 85  # 质量评分 0-100
      }
    """
    import anthropic

    import httpx
    client = anthropic.Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        base_url=os.getenv("ANTHROPIC_BASE_URL"),
        http_client=httpx.Client(trust_env=False),
    )

    # 构建术语核查清单
    term_checklist = []
    uncovered = []
    for t in terms:
        if t["in_glossary"] and t["ja"]:
            term_checklist.append(f'  · 「{t["zh"]}」→ 应译为「{t["ja"]}」')
        else:
            uncovered.append(t["zh"])

    checklist_str = "\n".join(term_checklist) if term_checklist else "  （无收录术语）"
    uncovered_str = "、".join(uncovered) if uncovered else "无"

    # 根据 style 决定语体指导
    if style == "marketing":
        style_guide = (
            "语体风格：营销推广文案，参考乐天证券（楽天証券）的表达习惯。"
            "语气亲切自然，允许使用です/ます体，可适当使用口语化表达，"
            "避免过于生硬的书面语。"
        )
    else:  # formal（默认）
        style_guide = (
            "语体风格：正式产品文案，参考SBI证券（SBI証券）的表达习惯。"
            "使用严谨的书き言葉体，以だ/である体为准，"
            "术语表达规范统一，避免口语化或模糊表达。"
        )

    system_prompt = f"""你是一位资深中日金融翻译审校专家。
你的任务是审查翻译初稿，修正错误，输出最终版本。

{style_guide}

输出规则：
1. 只输出 JSON，不要输出其他内容
2. JSON 格式如下（严格遵守）：
{{
  "final": "修正后的完整日语译文",
  "issues": ["发现的问题1", "发现的问题2"],
  "score": 85
}}
3. issues 为空数组时写 []
4. score 为 0-100 的整数，反映初稿质量（100=无需修改）"""

    user_prompt = f"""## 中文原文
{source_text}

## 翻译初稿（DeepL）
{draft}

## 金融术语核查清单（必须逐一核查）
{checklist_str}

## 未收录词汇（{uncovered_str}）
以上词汇在术语表中没有标准译法，请根据上下文给出合理翻译并在 issues 中说明处理方式。

## 审校要求
1. 逐一核查术语清单，确认每个术语是否正确出现在初稿中
2. 若术语被 DeepL 翻译为错误形式，在 final 中修正
3. 检查全文语体是否符合指定风格（{style}）
4. 检查数字格式（半角数字，百分号用%）
5. issues 只列真实问题，无问题不要捏造"""

    message = client.messages.create(
        model="claude-opus-4-6",  # 后处理用强模型保证质量
        max_tokens=2048,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = message.content[0].text.strip()
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        # 解析失败时返回初稿，不阻断流程
        return {
            "final": draft,
            "issues": ["[审校解析失败，返回初稿]"],
            "uncovered": uncovered,
            "score": 0,
        }

    try:
        data = json.loads(match.group())
    except json.JSONDecodeError:
        return {
            "final": draft,
            "issues": ["[审校解析失败，返回初稿]"],
            "uncovered": uncovered,
            "score": 0,
        }
    data["uncovered"] = uncovered
    return data
