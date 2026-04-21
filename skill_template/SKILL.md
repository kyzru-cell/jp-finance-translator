---
name: lark-cn2jp-finance
version: 2.0.0
description: "中日金融专业翻译：DeepL+Claude三段式流水线（术语识别→DeepL翻译→审校），支持单段文本、飞书文档、飞书表格三种模式。当用户需要中翻日、翻译金融报告/日报/研报/产品文案、将飞书文档/表格翻译成日语时使用。支持 --style formal（正式产品文案，SBI风格）和 --style marketing（营销推广，乐天风格）。"
user_invocable: true
metadata:
  requires:
    bins: ["lark-cli", "python"]
---

# 中日金融专业翻译 v2

> **词汇表：** 翻译由 DeepL+Claude 流水线自动执行，内置 1200+ 金融术语词库。
> **飞书操作前置：** 先阅读 [`../lark-shared/SKILL.md`](../lark-shared/SKILL.md)。

---

## 翻译流水线

所有翻译均通过三段式 Python 流水线执行，**不要用 Claude 直接翻译**：

```
中文输入
  → Claude Haiku（识别金融术语，查glossary）
  → DeepL API（带1200+术语表强制替换）
  → Claude Opus（审校术语/语体/数字格式）
  → 输出最终译文 + 质量评分
```

**项目路径：** `{{PROJECT_DIR}}/`

---

## 模式一：单段文本翻译

用户发来中文文本时，直接调用流水线：

```bash
cd {{PROJECT_DIR}}
python -X utf8 main.py translate "要翻译的中文" --style formal --verbose
```

- `--style formal`：正式产品文案（SBI书き言葉风格，**默认**）
- `--style marketing`：营销推广文案（乐天口语化风格）
- `--verbose`：显示识别到的术语和审校问题

**输出示例：**
```
原文：公司净利润同比增长15%
译文：当社の当期純利益は前年同期比15%増加した。
质量评分：92/100
识别术语：净利润→当期純利益（已收录）
```

---

## 模式二：飞书文档翻译

用户提供飞书文档链接，读取全文，逐段翻译，生成新的双语对照文档。

### Step 1：读取原文档

```bash
lark-cli docs +fetch --doc "<文档URL或token>" --format pretty
```

### Step 2：逐段翻译

对每个段落调用流水线（对话中直接执行，不需要脚本）：

```bash
cd {{PROJECT_DIR}}
python -X utf8 main.py translate "<段落文本>" --style formal
```

### Step 3：创建双语文档

将翻译结果组织为双语 Markdown，然后创建新文档：

```bash
lark-cli docs +create \
  --title "<原标题>【中日対訳版】" \
  --markdown "<完整Markdown内容>"
```

**双语格式：**
```markdown
# {原标题} / {日語タイトル}

---

**【中文】** {原段落}

**【日本語】** {译文}
```

**注意：**
- 创建文档前先告知用户标题，确认后执行
- 超过 10 段时每 5 段翻译一次，避免单次输出过长
- 图表说明、数字、英文专有名词保持原样

---

## 模式三：飞书表格翻译（填写日语列）

用户提供飞书表格链接，自动读取「中」列，翻译后填入「日」列。

```bash
cd {{PROJECT_DIR}}
python -X utf8 scripts/fill_lark_sheet.py "<表格URL>" --style formal
```

**预览模式（不写入，仅确认列识别正确）：**
```bash
python -X utf8 scripts/fill_lark_sheet.py "<表格URL>" --dry-run
```

**脚本行为：**
1. 自动识别第一行表头中的「中」列和「日」列
2. 跳过「日」列已有内容的行（不覆盖）
3. 逐行翻译并写回飞书表格

---

## 常见场景对照

| 用户说 | 使用模式 | style 参数 |
|--------|---------|-----------|
| "翻译这段话" / 直接粘贴中文 | 模式一 | formal |
| "翻译这篇飞书文档" | 模式二 | formal |
| "帮我填这个表格的日语列" | 模式三 | formal |
| "营销文案翻译成日语" | 模式一/三 | marketing |
| "查一下'回购'的日语怎么说" | 术语查询（直接回答）| — |

---

## 权限

| 操作 | 所需 scope |
|------|-----------|
| 读取飞书文档 | `docx:document:readonly` |
| 创建飞书文档 | `docx:document` |
| 读取飞书表格 | `sheets:spreadsheet.meta:read` |
| 写入飞书表格 | `sheets:spreadsheet:write_only` |

---

## 注意事项

- 金融术语宁可生硬也不意译，保持术语一致性
- 中国特有概念（A股、科创板、城投债）保留中文原名并加说明
- 质量评分低于 60 的段落，在输出时标注 ⚠️ 提示人工复核
- 飞书写入前务必先 `--dry-run` 确认列识别正确
