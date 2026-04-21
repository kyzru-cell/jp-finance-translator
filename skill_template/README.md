# 中日金融专业翻译 Skill

> 将中文金融文本翻译为日语，内置 1200+ 金融术语词库，支持飞书文档与表格直接写回。

---

## 翻译流程

```
中文输入
  ↓ Claude Haiku  — 识别金融术语，查词库匹配
  ↓ DeepL API    — 带术语表强制替换翻译
  ↓ Claude Opus  — 审校术语/语体/数字格式
  ↓
最终译文 + 质量评分（0–100）+ 审校问题列表
```

---

## 使用方式

在 Claude Code 会话中，直接用自然语言描述需求即可触发：

| 说法示例 | 触发模式 |
|---------|---------|
| 「翻译这段话：……」 | 单段翻译 |
| 「帮我翻译这篇飞书文档 https://…」 | 飞书文档 → 新建双语文档 |
| 「填这个表格的日语列 https://…」 | 飞书表格 → 写回日语列 |
| 「这几个词的日语怎么说」 | 术语查询 |

---

## 三种模式

### 模式一：单段文本翻译

直接粘贴中文，输出日语译文、质量评分、识别到的术语。

**示例输入：**
```
翻译：公司净利润同比增长15%，ROE 提升至12.3%
```

**输出：**
```
【原文】公司净利润同比增长15%，ROE 提升至12.3%

【译文】当社の当期純利益は前年同期比15%増加し、ROEは12.3%に上昇した。

质量评分：92/100
识别术语：净利润 → 当期純利益（已收录）/ ROE → ROE（已收录）
```

---

### 模式二：飞书文档翻译

提供飞书文档链接，读取全文逐段翻译，自动创建新的双语对照文档。

**示例输入：**
```
翻译这篇文档：https://futu.jp.feishu.cn/docx/xxxxxx
```

**输出文档格式：**
```
原标题【中日対訳版】

**【中文】** 原段落内容
**【日文】** 译文内容
```

> 创建文档前会先确认标题，超过 10 段时分批翻译。

---

### 模式三：飞书表格写回

提供飞书表格链接，自动识别「中」列，翻译后填入「日」列，已有内容的行跳过不覆盖。

**示例输入：**
```
帮我填这个表格的日语列：https://futu.jp.feishu.cn/sheets/xxxxxx
```

**执行流程：**
1. 读取表格，识别表头中的「中」列和「日」列
2. 逐行翻译（跳过日语列已有内容的行）
3. 写回飞书表格

> 建议先说「先 dry-run 确认一下」，预览列识别结果再正式写入。

---

## 语体风格

通过 `--style` 参数控制译文风格：

| 参数 | 风格 | 适用场景 | 参照基准 |
|------|------|---------|---------|
| `formal`（默认）| 正式书面体 | 产品说明书、条款、研报 | SBI 证券文案 |
| `marketing` | 口语化营销体 | 活动推广、开户引导、广告 | 乐天证券文案 |

**示例：**
```
翻译这段营销文案（用 marketing 风格）：现在开户享手续费全免
```

---

## 术语词库

内置 1200+ 金融术语，涵盖：

| 来源 | 词条数 | 内容 |
|------|--------|------|
| 手工整理 | 163 | 财务报表、证券市场、宏观经济等基础术语 |
| 富途内部词库 | 348 | 富途券商平台专业术语 |
| 楽天証券手册 | 126 | 乐天 MarketSpeed II 平台术语（口语化） |
| SBI 证券平台 | 40 | HYPER SBI 平台术语（正式书面） |
| JPX 官方词库 | 541 | 日本交易所集团官方金融术语 |

词库文件：`{{PROJECT_DIR}}/glossary/glossary.md`

更新词库后执行同步：
```bash
cd {{PROJECT_DIR}}
python main.py glossary sync
```

---

## 质量评分说明

| 评分范围 | 含义 | 建议 |
|---------|------|------|
| 80–100 | 译文质量高，可直接使用 | ✅ 直接使用 |
| 60–79 | 基本准确，少量问题 | 建议快速过一遍 |
| < 60 | 存在术语错误或语体问题 | ⚠️ 人工复核 |

---

## 安装与配置

### 前置要求

| 依赖 | 版本要求 | 获取方式 |
|------|---------|---------|
| Python | 3.10+ | python.org |
| DeepL API Key | Free 或 Pro 均可 | deepl.com/pro-api |
| Anthropic API Key | 企业代理 Key | 联系内部 IT |
| lark-cli | 最新版 | 内部分发 |

---

### Step 1：部署翻译项目

将项目放到本地任意路径，以下以 `{{PROJECT_DIR}}/` 为例。

安装 Python 依赖：

```bash
cd {{PROJECT_DIR}}
pip install -r requirements.txt
```

所需依赖包：

```
deepl>=1.18.0
anthropic>=0.25.0
typer>=0.12.0
rich>=13.0.0
python-dotenv>=1.0.0
httpx
openpyxl
python-docx
pdfplumber
```

---

### Step 2：配置 API 密钥

在项目根目录创建 `.env` 文件：

```
DEEPL_API_KEY=your-deepl-api-key
ANTHROPIC_API_KEY=your-anthropic-key
ANTHROPIC_BASE_URL=https://llm-proxy.futuoa.com/aws
```

> 企业内网用户：`ANTHROPIC_BASE_URL` 固定填写上方代理地址，`ANTHROPIC_API_KEY` 使用 `user-key-` 前缀的内部 Key。

---

### Step 3：上传术语表到 DeepL

首次使用前需将词库同步到 DeepL Glossary：

```bash
cd {{PROJECT_DIR}}
python -X utf8 main.py glossary sync
```

成功后输出 Glossary ID，自动保存到 `glossary/deepl_glossary_id.json`。

词库更新后重复执行此命令即可。

---

### Step 4：安装 Claude Code Skill

将 skill 文件夹放到 Claude Code 的 skills 目录：

```
~/.claude/skills/lark-cn2jp-finance/
    SKILL.md          ← skill 主文件
    README.md         ← 本说明文档
```

> Claude Code 会自动扫描 `~/.claude/skills/` 目录，无需手动注册。放入后重启 Claude Code 会话即生效。

---

### Step 5：配置飞书权限（模式二/三需要）

模式二（飞书文档翻译）和模式三（飞书表格写回）需要 lark-cli 权限：

```bash
# 授权读取和创建飞书文档
lark-cli auth login --scope "docx:document,docx:document:readonly"

# 授权读写飞书表格
lark-cli auth login --scope "sheets:spreadsheet.meta:read,sheets:spreadsheet:write_only"
```

完整权限清单：

| 操作 | 所需 scope |
|------|-----------|
| 读取飞书文档 | `docx:document:readonly` |
| 创建飞书文档 | `docx:document` |
| 读取飞书表格 | `sheets:spreadsheet.meta:read` |
| 写入飞书表格 | `sheets:spreadsheet:write_only` |

---

### 验证安装

```bash
cd {{PROJECT_DIR}}
python -X utf8 main.py translate "净利润同比增长15%" --verbose
```

输出中出现质量评分（如 `92/100`）且术语被正确识别，说明安装成功。

---

## 环境要求（汇总）

| 依赖 | 说明 |
|------|------|
| `{{PROJECT_DIR}}/` | Python 翻译项目 |
| `.env` 中的 `DEEPL_API_KEY` | DeepL 翻译 API |
| `.env` 中的 `ANTHROPIC_API_KEY` | Claude API（企业代理） |
| `lark-cli` | 飞书文档/表格读写（模式二、三需要） |

---

## 维护与更新

### 日常维护：扩充词库（最高频操作）

发现译文有误或缺词时，编辑词库文件，然后同步到 DeepL：

```bash
# 1. 编辑词库（在对应章节末尾添加一行）
# 文件：{{PROJECT_DIR}}/glossary/glossary.md
# 格式：| 中文 | 日语 | 场景 | 注 |

# 2. 同步到 DeepL（每次改完都要执行）
cd {{PROJECT_DIR}}
python -X utf8 main.py glossary sync
```

新词来源：
- 翻译时加 `--verbose` 输出的**未收录词汇**列表——最直接的缺口信号
- 业务同事反馈的错误术语

---

### 提升翻译质量

质量评分持续低于 60 通常是三类原因：

| 原因 | 解决方式 |
|------|---------|
| 术语缺失 | 补 `glossary.md` 并 sync |
| 语体不符合预期 | 调整 `post_processor.py` 对应 style 的 prompt |
| DeepL 处理特定句式差 | 在 `pre_processor.py` 的 system_prompt 加示例 |

---

### 更新 Skill 本身

修改翻译逻辑后，同步更新 `SKILL.md` 的说明，并手动递增版本号：

```
# SKILL.md frontmatter
version: 2.1.0   ← 手动递增
```

---

### 依赖与 API Key 管理

```bash
# 更新 Python 依赖包
pip install --upgrade deepl anthropic

# 查看当前 DeepL Glossary 状态（确认 Key 有效）
python -X utf8 main.py glossary list
```

Key 轮换只需修改 `.env` 文件，无需改代码：

```
DEEPL_API_KEY=新的Key
ANTHROPIC_API_KEY=新的Key
```

> DeepL Free 每月限额 50 万字符，超出会报错。超量时升级为 Pro 并替换 Key 即可。

---

## 常见问题

**Q：翻译结果中某个术语不对怎么办？**
把正确的中日对照加入 `glossary/glossary.md`，然后执行 `python main.py glossary sync` 更新到 DeepL，下次翻译即生效。

**Q：飞书表格找不到「中」列或「日」列？**
确认表格第一行（表头行）中有单元格内容恰好为「中」和「日」（单个字）。

**Q：如何只查词不翻译全文？**
直接问「'回购'日语怎么说」，skill 会直接查词库回答，不会走完整流水线。
