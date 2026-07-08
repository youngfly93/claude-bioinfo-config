---
name: bio-report
description: >-
  生成中文生信分析 Word 交付报告。配合 document-skills:docx，按 plan.md 组织章节，
  嵌入 results/figures 图表，套用中文排版规范（宋体正文 / Times New Roman 数字 / 黑体标题），
  生成后用 docx_check.py 验证 XML 完整性、图片引用、字体嵌入、markdown 残留与 AI 套话。
  触发条件：用户说"生成报告"、"出 Word 报告"、"bio-report"、"交付报告"、"写分析报告"、"生信报告"。
  完整交付、打包、发客户请优先使用 bio-deliver；本 skill 只负责报告生成/修订。
  不适用于：交付打包成 ZIP（用 bio-deliver）、论文稿件写作（用 nature-writing/nature-polishing）、PPT（用 bio-ppt）。
---

# 生信 Word 交付报告

配合 `document-skills:docx` 生成中文生信分析 Word 交付报告。

> 完整交付场景优先用 `bio-deliver`。本 skill 是报告专项能力，可被 `bio-deliver` 编排，也可在只需要生成/修订 Word 报告时单独使用。
>
> **用 Opus 4.6 生成**：委派给 `bio-report-writer` 子代理——它的模型固定为 `claude-opus-4-6`，独立运行、不影响主会话模型；它按本 skill 的规则执行。

## 前置准备

1. 读 `plan.md` 了解项目背景、分析内容和要求
2. 扫描 `results/`、`figures/` 收集所有可用图表和结果
3. 按 plan.md 的分析步骤确定报告章节结构

## 数值溯源（写进报告的每个数都不能编）

报告是客户第一眼看的东西，写错或编造一个数最贵（曾有结论写反、p 值 bug 进了 Word）。所以：

- 报告里每个数值、统计量、p 值、样本数，**必须来自 `results/` 里的真实结果文件**——不从图里或记忆"读个大概"，不凑整。
- 每个承重数值**登记到 `report_claims.tsv`**（报告位置 → 数值 → 来源文件:列）——这正是交付前 `bio-result-audit` 数字台账要逐条复算对账的清单。
- 拿不准的数 → 标"待核"，**先别写上去**（守全局"数字不杜撰"）。

## 报告结构模板

```
1. 项目概述（研究背景 / 分析目标 / 数据概况）
2. 分析方法（数据质控 / 分析流程 / 软件与参数）
3. 分析结果（按 plan.md 的每个分析步骤，每步配对应图表）
4. 结论与讨论
附录（A. 软件版本  B. 参数配置）
```

## 格式要求

- **中文正文**：宋体（SimSun），小四（12pt）
- **英文/数字**：Times New Roman，12pt
- **标题**：黑体（SimHei）— 一级三号(16pt)加粗 / 二级四号(14pt)加粗 / 三级小四(12pt)加粗
- **行距**：1.5 倍
- **页边距**：上下 2.54cm，左右 3.18cm

## CJK 安全渲染（防字体丢失 / 表格重叠）

报告最常翻车的是渲染：客户端缺字体、PDF 转换丢中文、表格文字重叠。固定走下面的安全路径，别临场发挥。

### Word(.docx)

- 字体按上方规范设定，并**嵌入字体**（embedTrueTypeFonts），客户没装宋体/黑体时也不被替换。
- 三线表显式设定列宽，避免内容溢出页面。

### PDF（Word→PDF、一页纸说明、`00_交付说明` 等）

- **中文字体一律用 Noto Sans CJK / 思源黑体宋体，严禁 Helvetica 或默认 Latin 字体**——这是 CJK 丢字、变方块的头号原因。
- **用 Python 渲染脚本生成，不用 shell heredoc/echo**（中文经 shell 易乱码，是高频报错源）。
- 表格设固定/自适应列宽 + 自动换行，渲染后确认无文字重叠、无溢出。
- **打包前先出一张预览（首页或关键页）给用户确认，再定稿**，别盲打包。

## 图表嵌入规则

1. 嵌入前验证图片路径存在（`ls -la "$img_path"`）
2. PDF 转图的 `_page1`/`_page2` 变体优先用 `_page1`
3. 标题格式：`图 X. 描述` / `表 X. 描述`，居中显示
4. 支持 .png/.jpg/.tiff
5. 表格用三线表风格；图表编号连续，与正文引用一致
6. 若报告需**新生成或重画**任何图（汇总图、占位补图等），脚本顶部统一
   `source(file.path(Sys.getenv("CLAUDE_PLUGIN_ROOT", "~/.claude"), "assets/figure-style/nature_theme.R"))`，优先用 `nature_*` 模块
   （volcano/km/enrich_dot/pca/box_sig/forest/oncoprint/heatmap）+ `save_nature()` 导出——
   和交付其余图一套风格、CJK 安全；不用 Python 画图。

## 生成后验证

用确定性脚本校验，不靠肉眼或裸正则（脚本扫**可见文字**而非裸 XML，避免误报）：

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/docx_check.py check <report.docx>
# 若无 ${CLAUDE_SKILL_DIR}：~/.claude/skills/bio-report/scripts/docx_check.py
# 检查 XML 完整性 / 图片引用对账 / 字体嵌入 / Markdown 残留
# 退出码 0=通过，1=有 WARN/FAIL
```

脚本报告的问题逐项处理：

- **Markdown 残留**：人工确认后清除（脚本只标不删）。
- **图片不一致**：核对断链或未被引用的图片。
- **字体未嵌入**：重新生成时开启字体嵌入。
- **AI 套话**：用 `bio-ai-clean` 扫描（关键词真源 `${CLAUDE_PLUGIN_ROOT:-$HOME/.claude}/skills/bio-deliver/scripts/ai_trace_scan.py`）。

## 注意

- 用 document-skills:docx 的能力生成 .docx
- **写人话 + 语气锚**：专业、自然的中文交付语气；别堆 AI 套话（"综上所述/值得注意的是/不难发现"），结论要具体、有数据支撑，不空泛。**动笔前先找交付人自己写过的报告/`00_交付说明` 当风格样本**，对齐其行文习惯（句子长短、要点密度、结论是否带具体数字、少逐词中英对照、别过度工整对称）——正式 Word 报告仍守上方排版规范（宋体/TNR/黑体、全角），但**措辞语气照作者、不套教科书模板**（详见 `bio-deliver` 的「语气锚」）。事后再用 `bio-ai-clean` 兜底扫一遍。
- 报告生成后通常接 `bio-deliver` 打包交付
