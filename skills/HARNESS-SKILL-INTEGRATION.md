# harness_bio ↔ bio-* skill 整合方案

> 状态：**方案文档，未改任何代码**。供本人与并行会话参考后再决定执行。
> 写于 2026-05-23。

## 背景

- **harness_bio**（GitHub: youngfly93/harness_bio，本地 `<workspace>/yang_lab/harness_bio`）：从 116 个真实生信外包 session 提炼的**工程级、契约化、可测试**治具（32 测试全绿，9.6/10）。file-based，agent 无关。
- **bio-\* skill 套件**（`~/.claude/skills/`，Codex 同步）：本会话陆续建的 11 个 skill，agent-facing，自动触发。
- 两者**同一领域、不同层次**。问题：bio-* skill 在审计/AI 扫描/打包等处**平行重实现**了 harness 已有且更严谨的东西，关键词等出现**二次分叉**。

## 两套系统的层次

| | harness_bio | bio-* skill |
|---|---|---|
| 形态 | 项目内文件 + bash 脚本 + 契约(QC断言/TSV/JSON schema) | ~/.claude/skills 提示词，自动触发 |
| 强项 | 机器可校验、可测试、确定性、深层 type 指南 | 自然语言触发、对话式、Codex 双引擎、补空白能力 |
| 弱项 | 需手动调用、无对话入口、无 Codex 集成 | 纯提示词、无机器校验、易和 harness 分叉 |

## 重叠与重复地图

| 领域 | harness（更成熟，宜作真源） | skill | 关系 |
|---|---|---|---|
| 脚手架 | `scaffold.sh` | bio-project-init | ✅ 已是瘦壳（调 scaffold.sh）——**整合范本** |
| 结果审计 | `validate.sh`+`run_audit.sh`+`auditor/PROMPT.md`+`audit_schema.json` | bio-result-audit | 🔴 平行 |
| 审计+修复 | `loop.md` Phase 3（5 轮协议） | bio-audit-fix | 🔴 平行 |
| 图表审查 | `quality/fig_review.md`（火山/热图/UMAP 专项） | bio-fig-review | 🟡 harness 更细 |
| **AI 痕迹扫描** | `delivery/ai_scan.sh`+`delivery_config.yaml`（28 词，config 驱动，有测试） | bio-ai-clean + `bio-deliver/scripts/ai_trace_scan.py`（两级 HARD/SOFT） | 🔴 **双实现双词表，已分叉** |
| 打包交付 | `delivery/package.sh`（validate→scan→ZIP→MD5） | bio-deliver + `zip_pack.py` | 🔴 双打包 |
| 报告 | `types/report.md` + 数值契约 | bio-report | 🟡 harness 有契约 |
| 开工前对齐 | `specs/plan_template.md` + `preflight_check.sh`（验证 plan） | bio-grill（访谈填 plan） | 🟢 **绝配互补** |
| 调试踩坑 | `known_issues.md`（116 session Top10） | bio-diagnose + `PITFALLS.md` | 🟢 互补，known_issues 更权威 |
| 项目地图 / 新见解 | （无） | bio-zoom-out / bio-roundtable | 🟢 skill 独有，补空白 |

## 目标架构：harness = 引擎，skill = 适配器 + 前端

```
用户自然语言意图
   │ 触发
   ▼
bio-* skill（前端：对话、触发、Codex 同步）
   │ 探测到 harness?
   ├─ 是 → 调用 harness 脚本/文档（唯一真源、机器可校验、有测试）
   └─ 否 → 回退到 skill 内置的轻量提示词逻辑（保证脱离 U 盘也能用）
```

三类角色：
1. **引擎（harness）**：唯一真源。scaffold/validate/ai_scan/package/run_audit + types/* + known_issues + 契约。
2. **适配器 skill**：bio-project-init（已是）、bio-result-audit、bio-audit-fix、bio-fig-review、bio-report、bio-ai-clean、bio-deliver → 改为"探测到 harness 就驱动它，没有则回退"。
3. **纯前端 skill**（harness 没有的能力，保持独立）：bio-grill、bio-zoom-out、bio-diagnose、bio-roundtable。

## 关键技术设计：路径探测 + 回退（不能硬绑 U 盘路径）

harness 在 U 盘固定路径，skill 直接写绝对路径 → U 盘未挂载/服务器/Codex 端全断。约定一个探测顺序：

```
HARNESS_DIR 探测优先级：
1. 环境变量 $HARNESS_BIO（若设置）
2. 当前项目内 ./harness/ （scaffold 生成的项目自带引用）
3. 已知安装路径 <workspace>/yang_lab/harness_bio
→ 三者都不存在：跳过 harness，用 skill 内置的回退逻辑，并提示"未找到 harness，使用轻量模式"
```

每个适配器 skill 开头加这段探测；探测到则"用 harness 脚本"，否则"用内置 prompt"。**这样脱离 harness 仍可用，挂上 harness 自动升级为机器可校验。**

## 逐 skill 整合规格

| skill | 探测到 harness 时 | 回退（无 harness） |
|---|---|---|
| bio-project-init | 已调 `scaffold.sh` ✅ | 内置目录模板 |
| bio-result-audit | 跑 `validate.sh` + `run_audit.sh`，读 `auditor/PROMPT.md`，按 `audit_schema.json` 输出 | 现有五维提示词审计 |
| bio-audit-fix | 按 `loop.md` Phase 3，每轮调 `validate.sh` | 现有 ≤5 轮提示词循环 |
| bio-fig-review | 引用 `quality/fig_review.md` 的专项清单 | 现有 SKILL 内清单 |
| bio-report | 引用 `types/report.md` + 用 `numeric_reference.tsv↔report_claims.tsv` 契约 | 现有排版+验证清单 |
| bio-ai-clean / bio-deliver | **统一到一个扫描器**（见下） | — |
| bio-grill | 产出 plan.md **对齐 `plan_template.md`**，结束提示"可跑 `preflight_check.sh` 验证" | 现有确认单 |
| bio-diagnose | PITFALLS 引用/合并 `known_issues.md` | 现有 PITFALLS.md |

## 最紧急：AI 扫描器双份分叉（先修这个）

现状两套、词表已不同：
- harness `ai_scan.sh`（bash，config 驱动 28 词，有测试，但**无 HARD/SOFT 分级**——会把"综上所述"这类直接当命中）
- 我们 `ai_trace_scan.py`（python，**两级 HARD/SOFT**，SOFT 只标记不删——更安全，但词表与 harness 不同步）

三个候选（择一，目标=单一真源）：
- **A（推荐）**：把"两级 HARD/SOFT"思路并进 harness 的 `ai_scan.sh` + `delivery_config.yaml`（拆 `keywords_hard` / `keywords_soft`），让 harness 成为唯一扫描器；bio-deliver/bio-ai-clean 探测到就调 ai_scan.sh。
- **B**：反向——bio-deliver 的 `ai_trace_scan.py` 作真源，harness `ai_scan.sh` 改调它（但破坏 harness 的 bash 自包含与测试）。
- **C**：保留两套但用同一份 `delivery_config.yaml` 关键词，python 端只加 HARD/SOFT 分层逻辑。最小改动，仍是两实现但词表同源。

> 取舍：A 最干净且保住 harness 的可测试性；C 改动最小。B 不推荐（破坏 harness 自包含）。

## 建议执行顺序（待批准后再做）

1. **修 AI 扫描器分叉**（候选 A 或 C）——唯一已经在出 bug 的点。
2. **bio-result-audit / bio-audit-fix** 改为驱动 `validate.sh`/`run_audit.sh`/`loop.md`（含路径探测+回退）。
3. **bio-fig-review / bio-report** 引用 harness 的 `fig_review.md` / `types/report.md`。
4. **bio-grill** 产出对齐 `plan_template.md`，衔接 `preflight_check.sh`。
5. **bio-diagnose** 的 PITFALLS 引用 `known_issues.md`。
6. **bio-deliver** 与 harness `package.sh` 二选一或互调（最后做，最敏感）。

## 风险与护栏

- **GitHub 仓库**：harness 是已发布、有 32 测试的仓库。任何改 harness 的动作都要：先在分支、跑 `tests/run_tests.sh` 全绿、再合并。
- **路径耦合**：绝不硬写 U 盘绝对路径，一律走探测+回退（见上）。
- **Codex 端**：harness 脚本在 Codex 环境同样要能跑（bash 3.x 已兼容）；skill 已软链接同步。
- **并行会话**：bio-result-audit/bio-fig-review/bio-project-init 由并行会话建，整合这几个前先对齐，避免互相覆盖。
- **可逆性**：所有 skill 改动是覆盖式（git/重写可回退）；harness 改动走分支+测试。

## 开放决策（需你拍板）

1. AI 扫描器选 A / B / C？
2. 适配器 skill 是否接受"探测到 harness 才升级、否则回退"的双模式（vs 强依赖 harness）？
3. 是否允许动 GitHub 仓库（改 harness 的 ai_scan.sh / 加 skill 能力沉淀进 harness）？还是只动 skill 侧？
