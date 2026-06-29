# CLAUDE.md · 生信工作区操作政策（②工作区层 · 模板）

> 用法：复制到你**生信工作根目录**（所有分析项目的父目录）下，改名为 `CLAUDE.md`。
> cwd 在这棵树下时自动加载 → 给所有生信项目一套统一操作纪律。
> `<...>` 是占位符，按你这台机器/这个工作区填实后删掉尖括号。

多研究者 / 多项目生信工作区：每个顶层目录是一位合作者或一个共享资产，彼此独立。目录以 `ls` 为准。

## 工作纪律
- 开工前先读子项目自己的 `CLAUDE.md` 和 `plan.md`，照里面的指令和进度走。
- 合作者 / 项目目录互相独立，未经要求别改别人的目录。
- 重计算放服务器 `<compute-server>`，别压本地；传文件用 `<transfer-method，如 Tailscale / scp>`。
- 脚本按编号顺序执行；R 环境因项目而异，以脚本 `library()` 为准。
- 优先复用已有流程（如 `<已有流程目录>`），别重造轮子。
- 交付用 `bio-deliver`（含清 AI 痕迹 + 打包 ZIP）；审计用 `bio-result-audit` 对照 `plan.md`。

## 绘图（若没放进 ① 全局 CLAUDE.md，就放这——绘图是生信专属政策）
- 出图 / 重画**一律**用 `nature-figure` 的 **R 后端**（它问 Python/R 时直接选 R）；Python 只做数据分析，不画图。
- 脚本顶部 `source(<nature_theme.R 在本机的实际路径>)`，配色 / 主题 / 热图 / CJK 字体统一真源，一个交付一套风格。

## 文档卫生（项目内 md 单一真源，别堆多版本）
- **真源文件**（要更新就改它们、别另存新版）：`plan.md`（设计）· `spec.md`（执行+验收清单）· `HANDOFF.md`（当前状态快照）· `execution_log.md`（流水账 append）· `numeric_reference.tsv` / `report_claims.tsv`（数字）· `docs/analysis-decisions/`（关键决策）· `audit/<模块>.md`（**同名覆盖，别 round_N / v1.2.x 递增并存**）。
- 过程草稿 / 临时记录统一进 `.work/`（可随时删），不与真源、交付混放。
- 散落多版本要收口 → `bio-docs-tidy`；交付前 `bio-deliver` 只收真源、排除过程 md。
- 接手不熟的项目先看 `DOCS_INDEX.md`（若有），知道哪几个 md 才是权威。

## 多 agent（若同环境跑 Claude + Codex 协作，见仓库 AGENTS.md）
- 同一项目同一时刻只一个 writer；审核 / 验收方对交付物只读、只写 `audit/`；验收审 committed 冻结快照。
- 写前取项目根 `.bio_harness/.lock`（工具 `harness/lib/agent_lock.sh`）。
