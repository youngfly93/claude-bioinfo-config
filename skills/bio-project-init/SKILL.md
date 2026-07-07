---
name: bio-project-init
description: >-
  为生信外包/分析项目生成标准脚手架。用于新项目初始化，创建 plan.md、CLAUDE.md、execution_log.md、
  numeric_reference.tsv、report_claims.tsv，及分析/绘图分阶段的 scripts/analysis、scripts/figures、results、figures 等目录。
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
- 目录（**分析与绘图分阶段**，见下「目录与追溯约定」）：
  - `scripts/analysis/`（产结果表的分析脚本）、`scripts/figures/`（只读结果、出交付图的绘图脚本）；
  - `results/`（分析阶段数字真源，一步一子目录 `results/<NN_step>/`）、`results/rds/`（重对象/画图输入）；
  - `figures/`（绘图阶段渲染产物）、`reports/`、`delivery/`、`.work/`（过程草稿+一次性诊断图，可丢）。
- `delivery/结构说明.md`：拷自 `${CLAUDE_PLUGIN_ROOT:-$HOME/.claude}/harness/templates/delivery_structure.md`——交付时照这个标准结构摆（`bio-deliver` 的 `structure_check.py` 会强制）。
- `DOCS_INDEX.md`：真源清单（列出上面哪几个是权威文档）。

> 中文内容一律用 Write 工具写（别用 shell heredoc/echo，防 CJK 乱码）。

## 目录与追溯约定（先分析、后绘图）

流程默认**两阶段分离**：分析阶段把每个统计量落进结果表，绘图阶段只消费结果表。好处是数字天然可溯源、改图不重算（返修只重渲染）、一套 house 风格一次压。追溯链靠**约定填满已有产物**，不新造 manifest / 检查器。

- **一步一子目录，编号对齐**——路径可预测是可追溯的地基：
  ```
  scripts/analysis/02_deg.R      →  results/02_deg/deg.tsv
  scripts/analysis/03_enrich.R   →  results/03_enrich/kegg.tsv
  scripts/figures/fig_volcano.R  reads results/02_deg/  →  figures/volcano.pdf
  ```
- **脚本头标准契约块 = 审计面（强制）**。每个分析/绘图脚本顶部都写，让只有 `Read/Glob/Grep` 的审查 agent 一 `grep '^# '` 就能重建整条「步骤→脚本→输入→输出」链、判路径是否合理，无需跑脚本：
  ```r
  # 步骤: A2.1 DESeq2 差异表达
  # 上游: results/01_qc/filtered_counts.rds
  # 输出: results/02_deg/deg.tsv
  # 种子: 42   参数: FDR<0.05 |log2FC|>=1
  ```
  四行齐全是勾 `[x]` 的前提之一。绘图脚本的 `# 上游: results/…` 让「零重算」契约看得见——缺上游声明、或声明里出现原始数据/现算 = 信号。
- **链路复用现有真源，不另立表**：数字 result→`numeric_reference.tsv`/`report_claims.tsv`（填 `source_file`/`source_column` 指结果表格）；图 figure→`spec.md` 验收里标 `输入=results/…`；脚本→结果的产地写进 `execution_log.md`（append-only）。
- **绘图铁律**：绘图脚本**只读 `results/`、不在图脚本现算统计量**；画图需要的某个数不在结果表里 = 回分析阶段把它写进结果表，别在图里凑。分析阶段只画一次性诊断图（QC/PCA，进 `.work/`），不进交付。这条同时喂 `report_claims_check` / `numeric_reference_verify` 的数字对账护栏。

## 清爽纪律：只留必要文件（供审查、防中间文件堆积）

目标是审查 agent Glob 一眼、每个文件都能对上某一步、没有孤儿中间物。规则：

- **`results/` 与 `figures/` 只放必要产物**——每个文件都必须是某个脚本头 `# 输出:` 声明过的、且被下游（图/报告/`report_claims`）消费。审查 agent Glob 到 `results/` 里**没有任何脚本 `# 输出:` 声明它**的文件 = **孤儿**，作为审计发现列出。
- **一切可再生的中间物 → `.work/`（可随时删）**：纯计算缓存、临时对象、诊断图、探索脚本，都进 `.work/`。`results/rds/` **只收下游图真正要读、又不能落成 tsv 的对象**（Seurat / survfit / 热图矩阵等）；能落 tsv 的一律 tsv，别囤 rds。
- **交付只收必要集**：`bio-deliver` 只收真源 + `results/`/`figures/` 必要产物，`.work/` 天然排除。清爽不是交付时才扫，是**分析时就不往 `results/` 里扔垃圾**。
- 判断准则一句话：**这个文件删了能不能从脚本+上游重生？能 → 属 `.work/`；不能且被下游消费 → 属 `results/`。** 两者都不是 = 该删。

## spec.md 模板

职责写死、不抢真源：`plan.md` = 设计真源；`spec.md` = 只管执行步骤、状态、验收证据。**按「先分析、后绘图」两阶段组织**：`A` 段分析产出结果表、`F` 段绘图消费结果表。按分析类型预填几个阶段占位，具体步骤等 `bio-grill` 锁设计后再展开：

```markdown
# spec.md · <项目名> 执行清单

> 派生自 `plan.md`。`plan.md` 是设计真源；本文件只管执行步骤、状态和验收证据。
> 状态语法（harness 自定义，正则解析，非 GitHub 渲染）: `[ ]` 未开始 · `[~]` 进行中(@agent) · `[x]` 完成 · `[!]` 卡住
> `[x]` = 验收证据存在且可复核（文件 / 断言 / 表格行数 / 图件 / proof-audit 之一）；细节写 `execution_log.md`，承重数字写 `numeric_reference.tsv` / `report_claims.tsv`。
> 流程两阶段：**A 段分析**先把统计量落进 `results/`，**F 段绘图**只读 `results/` 出交付图、零重算。

## A · 分析阶段（产出结果表，不出交付图）
- [ ] **A1.1 样本表检查** — 验收: `metadata/sample_sheet.tsv` 可读、sample_id 无重复、group >= 2
- [ ] **A1.2 QC 汇总** — 验收: `results/01_qc/multiqc.html` 存在（诊断图入 `.work/`，不进交付）
- [ ] **A2.1 DESeq2 差异表达** — 验收: `scripts/analysis/02_deg.R` → `results/02_deg/deg.tsv` 存在且含 `gene_id/log2FC/padj`
- [ ] **A3.1 富集分析** — 验收: `scripts/analysis/03_enrich.R` → `results/03_enrich/kegg.tsv` 存在且含 `ID/pvalue/geneID`

## F · 绘图阶段（只读 results/，零重算，出交付图）
- [ ] **F1 火山图** — 验收: `figures/volcano.pdf` 存在（nature_theme 风格）；输入 `results/02_deg/deg.tsv`
- [ ] **F2 富集气泡图** — 验收: `figures/kegg_dotplot.pdf` 存在（nature_theme 风格）；输入 `results/03_enrich/kegg.tsv`
```

- 每条任务**必须有「验收:」**，且验收是机器可核的证据，不是“做完了”的自评——没有证据就不能勾 `[x]`。
- 步骤号（A2.1 / F1）让 `execution_log.md` 与 git commit 都能引用对账；`[~]` 后挂 `@agent` 接写锁（谁持 `.bio_harness/.lock` 谁在写那步）。
- **F 段每条验收必带「输入 `results/…`」**——绘图消费的是结果表而非原始数据，缺输入声明就是"图脚本在现算"的信号。

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

- **绘图统一 house 样式 + 分阶段**：绘图集中在 `scripts/figures/`，脚本顶部 `source(file.path(Sys.getenv("CLAUDE_PLUGIN_ROOT", "~/.claude"), "assets/figure-style/nature_theme.R"))`，用 `theme_nature` / `save_nature` / `nature_heatmap` 出图——全项目一套风格、CJK 安全，出图走 `nature-figure` 的 R 后端。绘图脚本**只读 `results/` 结果表、不现算统计量**（见「目录与追溯约定」）。
- **数值溯源接数字台账**：`numeric_reference.tsv`（源数据真值）和 `report_claims.tsv`（报告里的数值声明）正是交付前 `bio-result-audit` 数字台账要逐条对账的两张表——边分析边填、承重数字都登记，审计时一对就清。
- **交接续接接 bio-handoff**：项目根放一份空 `HANDOFF.md`（当前状态快照），与 `execution_log.md`（流水账）分工不混——阶段交界 / 清理上下文前用 `bio-handoff` 更新它，接手或审批时按它再入水，防 `/clear`、`/compact` 后断层、口径不一。
- **文档卫生预埋**：建一个 `.work/`（过程/草稿集中、可随时删）和一份 `DOCS_INDEX.md`（真源清单：列出 plan/HANDOFF/报告/审计 等权威文档）。约定一事一文件、原地改、版本交 git，别堆 `_v2/_final/副本`；散落了用 `bio-docs-tidy` 收口。

## 纪律

- 不在用户未确认时覆盖已有项目文件。
- 不替用户编造数据来源、分组或 QC 数值。
- 生成后不要直接开跑分析；先补齐 `plan.md` → `bio-grill` 锁设计 → 展开 `spec.md`，再开跑。
- `spec.md` 与 `plan.md` 职责不互抢：plan=设计真源，spec=执行步骤+状态+验收证据；别把设计/阈值复制进 spec，也别在 plan 里记勾选状态。
- **先分析、后绘图不混阶段**：分析脚本进 `scripts/analysis/` 只产结果表，绘图脚本进 `scripts/figures/` 只读结果表；绘图缺数回分析阶段补进结果表，绝不在图脚本现算统计量。诊断图（QC/PCA）算一次性、进 `.work/`，不进交付。
