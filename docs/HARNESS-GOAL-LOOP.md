# Harness goal loop implementation notes

本改造把 `claude-bioinfo-config` 从 prompt/skill 配置进一步推进为“可验证交付 harness”。

## 设计边界

```text
CLAUDE.md      = 稳定个人偏好与科研纪律
skills/        = agent-facing adapter，负责触发、解释、编排
agents/        = 上下文隔离的审计/报告专家
hooks/         = 生命周期提醒与严格门控入口
harness/       = engine：唯一硬规则、唯一质量判定、唯一 proof 来源
```

## 闭环结构（双层 loop）

这套 harness 不是“一条直线管道”，而是**证明驱动的双层闭环**：完成与否由 `proof.py` / 退出码 / artifact 裁判，不由模型自评。

### 外层：goal loop（驱动整个交付到 PASS）

```text
        ┌─────────────────────────────────────────────────┐
        ↓                                                 │
  /goal 持续推进  →  harness 链                              │
   preflight → validate → audit → ai_scan → privacy → structure → package → collect
        ↓                                                 │
  proof.py 记录每步 exit_code + 日志 + P0–P3 发现             │
        ↓                                                 │
   全过？ ──否(P0/P1 或某步 exit≠0)──▶ 读结构化反馈 → 修复 ─────┘
        │                              (proof FAIL / blocker 清单 / stderr 日志)
        是
        ↓
  finalize 强校验(必需命令齐 + 全 exit0 + 有 zip + audit.json) → PASS / PASS_WITH_WARN
        ↓
  delivery_gate 放行
  [安全阀：连续 10 turn 仍不过 → 停，输出 blocker + proof 状态 + 最小修复建议]
```

### 内层：audit-fix loop（单点收敛，≤5 轮）

`bio-audit-fix`：审计 → 分级 P0–P3 → 修复 → **重审**，P0/P1 清零提前终止。
`bio-audit-fanout` 则是一次性**并行审计 + 对抗复核**（fan-out，非循环），适合大项目。

### 让它“真闭环”而非“带闸门的直线”的三点

1. **出不去除非真过**：`proof.py finalize` 拒绝 PASS（缺命令 / 有失败 / 无产物 → 置 FAIL），`delivery_gate` 查每条 `exit_code` —— 模型无法自评“做完了”蒙混。这是 loop 的闭合点。
2. **失败结构化反馈**：每步 `exit_code` + `stderr` 日志路径 + P0–P3 findings + finalize blocker 清单 → 模型据此修，而非瞎猜。
3. **状态持久、可续**：`proof.json` / `goal_proof.md` / `.bio_harness/logs/` / `audit/*.md` / `HANDOFF.md` 落盘，`/clear`、`/compact` 后接着转（防崩溃）。

### 诚实边界

harness 负责 **驱动判据 + 验证 + 反馈 + 状态 + 终止**；**实际的“改”与“重跑”由模型在 `/goal` 下完成**。`/goal` 是循环引擎，harness 是裁判 / 记分牌 / 跑道——只有在 `/goal` 下才自动转圈；手动跑一次 `bio-deliver` 是“带闸门的直线”，由人驱动迭代。对标 Anthropic long-running agents harness 范式（initializer + 失败清单 + 进度文件 + 一次推一个）。

## 新增能力

1. `skills/bio-goal`：生成 `/goal` completion condition。
2. `harness/specs/preflight_check.*`：开工前硬检查 plan、contract、sample sheet、reference lock。
3. `harness/quality/*`：样本表、contrast、reference、report claims、numeric claims、figure specs 的确定性 lint。
4. `harness/quality/run_audit.*`：生成机器可读 `audit/audit.json`。
5. `harness/delivery/ai_scan.*` / `package.*`：**复用** `bio-deliver` 的 `ai_trace_scan.py` / `zip_pack.py`（不另维护第二套；zip_pack 已做单一干净根目录、Windows 中文名安全）。
6. `harness/delivery/privacy_scan.py`：交付前隐私扫描（本机路径 `/Users`、内网 IP = P0，邮箱 = P1）。
7. `harness/delivery/structure_check.py` / `dedup_check.py`：交付结构合规（图/表放对位置）+ 去冗余（多版本/重复）两道 gate；标准结构模板 `harness/templates/delivery_structure.md`。
8. `harness/delivery/make_index.py`：自动生成 `00_目录导航.md`（想看什么→去哪 + 目录树）。
9. `harness/quality/{bulk_rnaseq,clinical_survival}_validator.py`：按分析类型的方法学 lint（contrast 方向 / 分组重复 / FDR-logFC / 删失编码 / cutpoint / PH 假设）。
10. `harness/delivery/proof.py`：命令级 proof wrapper（`init/run/collect/finalize/status --require-pass`）；finalize 强校验防手动 PASS；生成 `delivery/proof.json` 与 `goal_proof.md`。
11. `hooks/delivery_gate.py`：默认 advisory；`.bio_clinical_mode` / `.bio_delivery_gate` / `delivery/.ready_to_send` / `BIO_DELIVERY_GATE_STRICT=1` 任一触发 strict；查 proof 状态 + **每条命令 exit_code**。

## 建议 PR 标题

`feat: add harness goal loop and delivery proof gates`

## 建议 PR 描述

- Adds deterministic harness engine for bioinformatics delivery projects.
- Adds `bio-goal` skill and slash command to convert projects into verifiable Claude Code `/goal` loops.
- Adds proof artifacts (`delivery/proof.json`, `delivery/goal_proof.md`) and command wrapper.
- Adds preflight/quality/audit/AI trace/package scripts with stdlib-only Python.
- Adds advisory/strict delivery gate hook. Public `settings.json` sets `skipDangerousModePermissionPrompt=false` (safer default for a shared config; flip locally via `settings.local.json` if your workflow needs it). Delivery safety comes from the gate + strict mode (`BIO_DELIVERY_GATE_STRICT=1` / `.bio_delivery_gate` / `delivery/.ready_to_send`), not from per-action prompts.
