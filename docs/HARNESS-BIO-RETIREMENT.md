# harness_bio 退役决策记录

> 状态：**已执行**。`harness_bio` 仓库退役，能力并入本仓库（`claude-bioinfo-config`）。
> 本仓库的 `harness/` 是生信交付 harness 的**唯一真源**。

## 背景

历史上存在两套同源治具：

- **`harness_bio`**（独立 GitHub 仓库，从 116 个真实外包 session 提炼，曾标 32 测试全绿 / 9.6 同行评审）——早期工程级源仓库。
- **本仓库 `harness/`**（= 现役 `~/.claude/harness`）——在 `harness_bio` 基础上持续演进：新增 `proof.py`、`structure_check.py`、`privacy_scan.py`、`dedup_check.py`、`make_index.py`，以及全套 `*_check.py` / `*_validator.py`（numeric / report / reference / contrast / figure / bulk-rnaseq / clinical-survival）。

两者**双向漂移**：现役版有源仓库没有的新检查器；源仓库有现役版丢失的若干契约/经验文件。挂着「32 测试全绿」招牌的源仓库，实际已不是现役引擎——这种「两个半真源」是最糟的中间态。

## 决策

**`harness_bio` 退役、归档为只读**（保留历史与 32 测试记录），不再作为真源或被引用。退役前已把它独有、现役版缺失的能力**抢救并入本仓库**。

## 抢救清单（已并入 `harness/`）

| 文件 | 作用 | 落位 |
|---|---|---|
| `known_issues.md` | 116 session 提炼的 Top10 高频错误 + 防护规则（P0–P2） | `harness/known_issues.md` |
| `audit_schema.json` + `auditor/PROMPT.md` + `audit_example.json` | LLM 审计代理（bio-result-auditor）的**结构化输出契约**，喂 audit→fix→reaudit 5 轮循环（`dimensions`/`action_items`/`round`）。与现役确定性 `run_audit.py`（产 `audit.json`）互补，不重复 | `harness/quality/` |
| `audit.md` | 上述审计契约的人读说明 | `harness/quality/audit.md` |
| `loop.md` | audit→fix→reaudit 五轮协议规格 | `harness/loop.md` |
| `fig_review.md` | 火山图 / 热图 / UMAP 专项审查清单 | `harness/quality/fig_review.md` |

**有意丢弃（已废）**：`delivery_config.yaml` + `read_config.sh` + `standards.md` —— AI 痕迹扫描已统一到 `skills/bio-deliver/scripts/ai_trace_scan.py` 单一真源，`harness/delivery/ai_scan.sh` 仅 5 行转调它，旧的 config 驱动词表不再需要。

## 仍未还清的整合债（后续）

抢救只是把文件搬进来，**让 skill 真正驱动这些契约**是下一步。当前仅 4 个 skill 引用 harness（bio-deliver / bio-goal / bio-project-init / bio-result-audit）。计划中应改为「探测到 harness 就驱动、否则回退内置提示词」的还有：

| skill | 探测到 harness 时应做 | 当前状态 |
|---|---|---|
| bio-result-audit | 按 `quality/audit_schema.json` 输出，读 `auditor/PROMPT.md` | 已引用 harness，未对接 schema |
| bio-audit-fix | 按 `loop.md` 五轮协议，每轮跑 `quality/validate.sh` | 内置简版，未引用 loop.md |
| bio-fig-review | 引用 `quality/fig_review.md` 专项清单 | 内置清单，未引用 |
| bio-diagnose | PITFALLS 引用/合并 `known_issues.md` | 两份并存，未合并 |

> 路径耦合护栏：skill 一律走 `harness/lib/resolve_harness.sh` 探测（项目内 → `$CLAUDE_PLUGIN_ROOT` → `~/.claude/harness`），**绝不硬编码绝对路径**。

## 已确认安全

- 现役环境不依赖被退役的仓库：`resolve_harness.sh` 回退路径找的是通用安装位，未硬编码源仓库路径。
- 抢救文件经脱敏扫描：真实路径 / 用户名 / 服务器 / 客户名命中 **0**。
