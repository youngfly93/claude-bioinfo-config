# 全局工作约定（Claude Code · 所有项目通用）

> 只放所有项目都成立的规则；工作区专属的技术栈/交付细节写进该目录的 CLAUDE.md
> （如 `<workspace>/CLAUDE.md` 已覆盖生信工作区）。

## 关于用户
- 生物信息工程师，主做生信外包分析与交付（癌症基因组、多组学、蛋白组、临床报告）。
- 技术栈以 R/Bioconductor 为主，其次 Python，少量 Nextflow/Shell。
- 交付物多为 SCI 级图表、中文 Word 报告、ZIP 包。
- 默认用中文回答与注释。

## 绘图
- 出图/重画一律用 `nature-figure` 的 **R 后端**（它问 Python/R 时直接选 R）；Python 只做数据分析，不画图。
- 脚本顶部 `source("~/.claude/assets/figure-style/nature_theme.R")`（配色/主题/热图/导出/CJK 字体的统一真源），别每张图重定义，一个交付一套风格。
- 出复杂/复合生信图（oncoprint、circos 圈图、临床森林图、UMAP atlas、单细胞轨迹、多组学复合大图、富集网络、进化树+热图）先过 `nature-figure-archetypes` 的「图型野心阶梯」选型、落图前过「分析严谨护栏」，别默默退回基础柱状图；它仍 source 上面的 `nature_theme.R`，风格不另起。

## 科研严谨性（交付质量底线）
- 数字不杜撰：每个数值/统计量/p 值都来自真实结果文件、能溯源到脚本；不确定就标注，绝不编造或凑数。
- 版本与阈值显式化：参考基因组/注释、关键阈值（FDR/logFC/p）先确认或写明假设，别默默用默认值。
- 可复现：随机过程设种子、记录关键参数，不中途静默改设计或参数。
- 先对齐再开跑：高风险/交付/临床相关分析，开工前先确认设计（bio-grill 的精神）。
- 不擅自降级，遇阻先商量：装不上包/缺数据/跑不动等阻塞，绝不偷偷退而求其次用差方法蒙混——停下讲清「卡在哪 + 候选对策及代价」，商量定了再继续。
- 改文件前先 `git status` / `git diff` 展示差异，确认后再 commit。

## 文档卫生（防 md 冗余 / 多版本，少造误解）
- 一事一文件、**原地改**：要更新就改那个现成文件，别新建 `_v2 / _final / 副本 / (2)` 另一份；版本变更交给 git，不靠文件名堆。
- 新建任何记录/说明 md 前，**先查有没有该更新的现成文件**（plan / HANDOFF / 执行日志 / 审计记录等）。
- 过程记录与正本分开：过程/草稿集中放、可随时丢；只认少数真源文件，必要时用一份索引标明哪几个是权威。

## 多 agent 环境隔离（Claude Code / Codex）
- 本仓库只存配置源码、harness、skills、hooks、tests；不要把 `~/.claude` 或 `~/.codex` 的运行态缓存、历史、sessions、SQLite 日志、credentials/auth 文件纳入仓库。
- Claude Code 和 Codex 可以共同审核同一项目，但共享事实只认项目根下的 `audit/`、`delivery/proof.json`、`delivery/goal_proof.md`、`report_claims.tsv`、`numeric_reference.tsv`、`.bio_harness/logs/` 以及源数据/脚本。
- 验收时不用任一 agent 的聊天记录、缓存或主观总结作证据；若两边结论冲突，以 harness 退出码、`audit.json`、`proof.json` 和源表复算结果为准。
- 除非用户明确要求安装/同步配置，不从本仓库写回 `~/.claude/` 或 `~/.codex/`。
- **防并发写入污染**：同一项目同一时刻只允许一个 writer；审核/验收 agent 对交付物只读、只写 `audit/`、发现问题只标记不顺手改；验收只审 committed 冻结快照（核对 `proof.json` 的 `git_commit`/`plan_sha256` == 当前 checkout）。写前取项目根 `.bio_harness/.lock`（工具 `harness/lib/agent_lock.sh`，咨询式）。操作细节见 `AGENTS.md` 的「写入隔离与审核独立」。
- **审计文件用共享标准**：与 Codex 审同一项目时，审计发现写成 `audit/<module>.<agent>.md`（module 用 `plan.md` 任务名逐字、文件头记 `audited_commit`），各写各的、不互踩——防"各写各的、最后不是一个事儿"。格式与裁决规则的**单一真源**见 [`docs/SHARED-AUDIT.md`](docs/SHARED-AUDIT.md)；核对两边是否审同一版：`python3 harness/lib/audit_reconcile.py <项目根>`。
