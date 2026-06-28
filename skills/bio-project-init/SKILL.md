---
name: bio-project-init
description: >-
  为生信外包/分析项目生成标准脚手架。用于新项目初始化，创建 plan.md、CLAUDE.md、execution_log.md、
  numeric_reference.tsv、report_claims.tsv、results/figures/scripts/reports/delivery 等目录。
  触发条件：用户说"初始化生信项目"、"project-init"、"建项目脚手架"、"新建外包项目"、"创建 plan.md 模板"。
  不适用于：已有项目梳理（用 bio-zoom-out）、开工前分析设计确认（用 bio-grill）、交付打包（用 bio-deliver）。
---

# 生信项目初始化

为当前生信外包/分析项目生成标准目录和计划模板。这个 skill 会创建文件，执行前必须确认目标目录。

## 信息收集

先从当前目录推断，推断不了再问：

- 项目名称：中文名，如“心衰转录组分析”。
- 分析类型：`bulk_rnaseq`、`scrnaseq`、`multi_omics`、`custom`。
- 物种：`human`、`mouse` 或其他。
- 项目目录：默认当前目录。

如果当前目录已有 `plan.md`、数据文件或脚本，先说明会覆盖/冲突的风险，不能直接覆盖。

## 生成脚手架

确认后**自包含生成**（用 Write/`mkdir -p` 直接建，不依赖任何外部脚本或机器特定路径）：

- `plan.md`：**设计真源**——预填充分析计划，含背景/需求、数据、设计、阈值、contrast、QC 断言，`?` 占位符待补。**客户需求默认落「背景」段**，不单独建 requirements.md。
- `spec.md`：**执行+验收清单**，从 plan.md 拆出（设计锁定后展开）。状态语法 `[ ]`/`[~]`/`[x]`/`[!]`（harness 自定义、正则解析，非 GitHub checkbox 渲染）；每条带「验收:」机器可核证据。骨架见下「spec.md 模板」。
- `requirements.md`（**可选，不默认生成**）：仅当有客户合同 / 长邮件 / 聊天记录要整理时再建；否则需求记在 `plan.md` 背景段。
- `CLAUDE.md`：项目 agent 行为配置。
- `execution_log.md`：执行/审计流水账模板（append-only）。
- `HANDOFF.md`：当前状态快照空模板（见 `bio-handoff`，与流水账分工不混）。
- `numeric_reference.tsv` / `report_claims.tsv`：表头 `key\tvalue\tsource_file\tsource_column`（report_claims 用 `claim_id\tclaim\tvalue\tsource_file\tsource_column\tstatus`）。
- `reference.lock`：`organism / genome_build / annotation / created_at`（版本锁；先留 `?` 待确认）。
- 目录：`results/`、`figures/`、`scripts/`、`reports/`、`delivery/`、`.work/`（过程草稿，可丢）。
- `delivery/结构说明.md`：拷自 `${CLAUDE_PLUGIN_ROOT:-$HOME/.claude}/harness/templates/delivery_structure.md`——交付时照这个标准结构摆（`bio-deliver` 的 `structure_check.py` 会强制）。
- `DOCS_INDEX.md`：真源清单（列出上面哪几个是权威文档）。

> 中文内容一律用 Write 工具写（别用 shell heredoc/echo，防 CJK 乱码）。

## spec.md 模板

职责写死、不抢真源：`plan.md` = 设计真源；`spec.md` = 只管执行步骤、状态、验收证据。按分析类型预填几个阶段占位，具体步骤等 `bio-grill` 锁设计后再展开：

```markdown
# spec.md · <项目名> 执行清单

> 派生自 `plan.md`。`plan.md` 是设计真源；本文件只管执行步骤、状态和验收证据。
> 状态语法（harness 自定义，正则解析，非 GitHub 渲染）: `[ ]` 未开始 · `[~]` 进行中(@agent) · `[x]` 完成 · `[!]` 卡住
> `[x]` = 验收证据存在且可复核（文件 / 断言 / 表格行数 / 图件 / proof-audit 之一）；细节写 `execution_log.md`，承重数字写 `numeric_reference.tsv` / `report_claims.tsv`。

## S1 · 质控
- [ ] **S1.1 样本表检查** — 验收: `metadata/sample_sheet.tsv` 可读、sample_id 无重复、group >= 2
- [ ] **S1.2 QC 汇总** — 验收: `results/qc/multiqc.html` 存在

## S2 · 差异分析
- [ ] **S2.1 DESeq2 差异表达** — 验收: `results/deg/deg.tsv` 存在且含 `gene_id/log2FC/padj`
- [ ] **S2.2 火山图** — 验收: `figures/volcano.pdf` 存在（nature_theme 风格）
```

- 每条任务**必须有「验收:」**，且验收是机器可核的证据，不是“做完了”的自评——没有证据就不能勾 `[x]`。
- 步骤号（S1.1）让 `execution_log.md` 与 git commit 都能引用对账；`[~]` 后挂 `@agent` 接写锁（谁持 `.bio_harness/.lock` 谁在写那步）。

## 初始化后检查

1. 展示生成的 `plan.md` 摘要。
2. 列出所有 `?` 占位符，按类别提示用户补齐：
   - 项目背景、数据来源、实验设计。
   - 固定参数，如 DEG 阈值、分组定义、contrast。
   - QC 断言中的具体数值，如样本总数。
3. 验证关键文件和目录都已创建。
4. 跑一遍 harness 预检确认脚手架合规（缺项会以 P2/P3 提示，可选规格缺=P3 不阻断）：
   `bash "${CLAUDE_PLUGIN_ROOT:-$HOME/.claude}/harness/specs/preflight_check.sh" .`

## 输出

```markdown
## 项目脚手架结果

| 项 | 状态 | 路径/说明 |
|----|------|-----------|
| plan.md | ✅/❌ | ... |
| CLAUDE.md | ✅/❌ | ... |
| 标准目录 | ✅/❌ | ... |
| 未填占位符 | N | ... |

下一步：补齐 plan.md 的 `?` → bio-grill 锁设计 → 展开 spec.md 执行清单 → 开跑。
```

## 统一风格与溯源接线

脚手架建好后，让新项目从一开始就接上全局规范：

- **绘图统一 house 样式**：所有绘图脚本顶部 `source(file.path(Sys.getenv("CLAUDE_PLUGIN_ROOT", "~/.claude"), "assets/figure-style/nature_theme.R"))`，用 `theme_nature` / `save_nature` / `nature_heatmap` 出图——全项目一套风格、CJK 安全。出图走 `nature-figure` 的 R 后端。
- **数值溯源接数字台账**：`numeric_reference.tsv`（源数据真值）和 `report_claims.tsv`（报告里的数值声明）正是交付前 `bio-result-audit` 数字台账要逐条对账的两张表——边分析边填、承重数字都登记，审计时一对就清。
- **交接续接接 bio-handoff**：项目根放一份空 `HANDOFF.md`（当前状态快照），与 `execution_log.md`（流水账）分工不混——阶段交界 / 清理上下文前用 `bio-handoff` 更新它，接手或审批时按它再入水，防 `/clear`、`/compact` 后断层、口径不一。
- **文档卫生预埋**：建一个 `.work/`（过程/草稿集中、可随时删）和一份 `DOCS_INDEX.md`（真源清单：列出 plan/HANDOFF/报告/审计 等权威文档）。约定一事一文件、原地改、版本交 git，别堆 `_v2/_final/副本`；散落了用 `bio-docs-tidy` 收口。

## 纪律

- 不在用户未确认时覆盖已有项目文件。
- 不替用户编造数据来源、分组或 QC 数值。
- 生成后不要直接开跑分析；先补齐 `plan.md` → `bio-grill` 锁设计 → 展开 `spec.md`，再开跑。
- `spec.md` 与 `plan.md` 职责不互抢：plan=设计真源，spec=执行步骤+状态+验收证据；别把设计/阈值复制进 spec，也别在 plan 里记勾选状态。
