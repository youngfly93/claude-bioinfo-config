# AGENTS.md

本仓库是 `claude-bioinfo-config` 的生信交付 harness 真源。Codex 在这里工作时，把自己视为适配层；不要把交付规则复制进 prompt、wrapper 或新脚本。

## 先读什么

开工前按顺序读：

1. `CLAUDE.md`
2. `README.md`
3. `docs/HARNESS-GOAL-LOOP.md`
4. 需要改动具体 skill/hook/harness 时，再读对应目录下的文件

如果任务涉及历史取舍，读 `docs/HARNESS-BIO-RETIREMENT.md`，确认 `harness/` 是唯一真源。

## 架构边界

- `harness/` 是 engine：唯一硬规则、唯一质量判定、唯一 proof 来源。
- `skills/`、`commands/`、`hooks/`、`agents/` 是 adapter：负责触发、解释、编排，不重复实现质量规则。
- 不新增 `bin/bio-harness` 之类统一 CLI，除非用户明确要求；现阶段直接调用 `harness/` 里的脚本。
- 不为 Warp、Codex、Claude 分别维护一套规则。所有环境都必须落到同一套 harness 命令、`audit.json` 和 `proof.json`。

## 完成判定

不要主观判断“交付完成”。完成只能由以下证据判定：

- `delivery/proof.json`
- `delivery/goal_proof.md`
- `audit/audit.json`
- proof 中所有必需命令的 `exit_code`
- zip artifact 及其 md5

存在 P0/P1 时必须修复后重跑；P2/P3 可以记录为 warning，但不能伪装成无问题。

## 常用 harness 命令

优先从项目内解析 harness；没有项目内 harness 时，使用插件或全局安装位：

```bash
HARNESS_ROOT="$(sh harness/lib/resolve_harness.sh . 2>/dev/null || true)"
```

典型检查链：

```bash
bash "$HARNESS_ROOT/specs/preflight_check.sh" .
bash "$HARNESS_ROOT/quality/validate.sh" --strict .
bash "$HARNESS_ROOT/quality/run_audit.sh" .
python3 "$HARNESS_ROOT/delivery/proof.py" status --require-pass .
```

完整 goal loop 以 `harness/bin/bio_goal.sh` 输出为准，不手写替代完成条件。

## Review 口径

做审计或 review 时，优先检查：

- `plan.md`
- `report_claims.tsv` / `numeric_reference.tsv`
- `audit/audit.json`
- `delivery/proof.json`
- `delivery/goal_proof.md`
- 关键结果来源脚本和结果表

重点找 P0/P1：数字不可溯源、报告数字与源表不一致、contrast 方向错误、样本/分组错误、隐私泄漏、AI 痕迹、交付结构放错位置。

## 禁止事项

- 不读取、复制、提交凭据、会话历史、客户/患者数据。
- 不把 `~/.claude` 里的运行态缓存、history、sessions、credentials 纳入本仓库。
- 不在 `_archive`、`.tmp`、副本、`*_v2`、`*_final` 文件里改正事。
- 不新增第二套 AI 扫描、打包、proof、audit 逻辑；复用现有 harness 或 `skills/bio-deliver/scripts/`。
