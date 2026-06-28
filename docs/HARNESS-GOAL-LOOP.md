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

## 新增能力

1. `skills/bio-goal`：生成 `/goal` completion condition。
2. `harness/specs/preflight_check.*`：开工前硬检查 plan、contract、sample sheet、reference lock。
3. `harness/quality/*`：样本表、contrast、reference、report claims、numeric claims、figure specs 的确定性 lint。
4. `harness/quality/run_audit.*`：生成机器可读 `audit/audit.json`。
5. `harness/delivery/ai_scan.*`：AI 痕迹 hard/soft 扫描。
6. `harness/delivery/package.*`：manifest、zip、md5、verify。
7. `harness/delivery/proof.py`：命令级 proof wrapper，生成 `delivery/proof.json` 与 `goal_proof.md`。
8. `hooks/delivery_gate.py`：默认 advisory，检测 `.bio_delivery_gate` 或 `delivery/.ready_to_send` 后严格阻止未 proof 交付。

## 建议 PR 标题

`feat: add harness goal loop and delivery proof gates`

## 建议 PR 描述

- Adds deterministic harness engine for bioinformatics delivery projects.
- Adds `bio-goal` skill and slash command to convert projects into verifiable Claude Code `/goal` loops.
- Adds proof artifacts (`delivery/proof.json`, `delivery/goal_proof.md`) and command wrapper.
- Adds preflight/quality/audit/AI trace/package scripts with stdlib-only Python.
- Adds advisory/strict delivery gate hook and disables dangerous-mode prompt skipping by default.
