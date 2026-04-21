# jp-finance-translator

> 中日金融专业翻译工具 — DeepL + Claude 三段式流水线，内置 1200+ 金融术语词库。
> 作为 **Claude Code Skill** 运行，在对话中直接触发，支持单段文本、飞书文档、飞书表格三种模式。

---

## 安装

### 前置要求

| 依赖 | 版本 | 获取方式 |
|------|------|---------|
| Python | 3.10+ | python.org |
| Claude Code | 最新版 | [claude.ai/code](https://claude.ai/code) |
| DeepL API Key | Free / Pro 均可 | deepl.com/pro-api |
| Anthropic API Key | — | anthropic.com |

### 一键安装

```bash
git clone https://github.com/xiajing0522-creator/jp-finance-translator.git
cd jp-finance-translator
python install.py
```

安装脚本会自动完成：
1. 检查 Python 版本
2. 安装 Python 依赖（`pip install -r requirements.txt`）
3. 创建 `.env` 配置文件（填写 API Key 后继续）
4. 将 Skill 文件安装到 Claude Code
5. 同步术语表到 DeepL Glossary

安装完成后**重启 Claude Code 会话**即可使用。

---

## 在 Claude Code 中使用

安装后在任意 Claude Code 会话中，直接用自然语言触发：

### 单段文本翻译

```
> 翻译：公司净利润同比增长15%，ROE 提升至12.3%
```

```
【原文】公司净利润同比增长15%，ROE 提升至12.3%
【译文】当社の当期純利益は前年同期比15%増加し、ROEは12.3%に上昇した。
质量评分：92/100
识别术语：净利润 → 当期純利益 / ROE → ROE
```

### 飞书文档翻译

```
> 翻译这篇飞书文档：https://example.feishu.cn/docx/xxxxxx
```

自动读取全文，逐段翻译，创建新的双语对照文档。

### 飞书表格填写日语列

```
> 帮我填这个表格的日语列：https://example.feishu.cn/sheets/xxxxxx
```

自动识别「中」列，翻译后填入「日」列，已有内容的行跳过不覆盖。

### 术语查询

```
> "回购"日语怎么说？
```

```
回购 → 自社株買い（SBI正式文案）/ 自社株買いキャンペーン（乐天营销文案）
```

---

## 翻译风格

通过 `--style` 参数切换：

| 参数 | 风格 | 适用场景 |
|------|------|---------|
| `formal`（默认）| 正式书面体 | 产品说明书、条款、研报 |
| `marketing` | 口语化营销体 | 活动推广、开户引导 |

```
> 翻译这段营销文案（marketing 风格）：现在开户享手续费全免
```

---

## 翻译流水线

```
中文输入
  ↓ Claude Haiku  — 识别金融术语，查词库匹配
  ↓ DeepL API    — 带 1200+ 术语表强制替换翻译
  ↓ Claude Opus  — 审校术语 / 语体 / 数字格式
  ↓
最终译文 + 质量评分（0–100）+ 审校问题列表
```

---

## 术语词库

内置 1200+ 金融术语，涵盖：

| 来源 | 词条数 |
|------|--------|
| 手工整理（财务报表、证券市场、宏观经济） | 163 |
| 富途内部词库 | 348 |
| 楽天証券 MarketSpeed II | 126 |
| SBI 証券 HYPER SBI | 40 |
| JPX 日本交易所集团官方词库 | 541 |

更新词库后执行同步：

```bash
python main.py glossary sync
```

---

## 质量评分

| 评分 | 含义 | 建议 |
|------|------|------|
| 80–100 | 译文质量高 | 直接使用 |
| 60–79 | 基本准确，少量问题 | 快速过一遍 |
| < 60 | 存在术语错误或语体问题 | 人工复核 |
