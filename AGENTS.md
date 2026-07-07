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

## 生信项目结构契约（两个 agent 都遵循）

> Codex 不自动加载 `skills/*/SKILL.md`（那是 Claude 的 adapter）。凡需**绑定两个 agent** 的项目级约定，都在这里指过去——单一真源仍是对应 SKILL.md，本节只点、不复制，避免漂移。

新建或推进生信分析项目时，无论 Claude 还是 Codex 当 writer，都按 `skills/bio-project-init/SKILL.md` 的结构契约走：

- **先分析、后绘图分阶段**：`scripts/analysis/`（产结果表）与 `scripts/figures/`（只读 `results/` 出图、零重算）分开；绘图缺数回分析阶段补进结果表，绝不在图脚本现算统计量。
- **`results/<NN_step>/` 编号对齐**：脚本编号 ↔ 结果子目录一一对应，路径可预测。
- **脚本头四行契约（强制）**：每个分析/绘图脚本顶部写 `# 步骤: / # 上游: / # 输出: / # 种子:`——这是审查方（只有 `Read/Glob/Grep`）重建步骤地图的审计面。
- **清爽纪律**：`results/`+`figures/` 只留必要产物；可再生的中间物/诊断图进 `.work/`（可删）；`results/` 里无脚本 `# 输出:` 声明的文件 = 孤儿。

审计（无论谁当 auditor）除 §7 方法保真外，按 `skills/bio-result-audit/SKILL.md` 的「2.5 步骤地图 + 清爽体检」核：grep 脚本头重建 步骤→脚本→输入→输出 链、验路径合理性、揪孤儿/多余中间文件、查绘图是否现算。两边审同一套，才不会"各审各的"。

## 多 agent 环境隔离

Claude Code 与 Codex 可以在同一项目中分析、审核和验收，但运行态必须隔离：

- 仓库只存配置源码、harness、skills、hooks、tests；不存任何 agent 运行态。
- Claude 运行态留在 `~/.claude/`，Codex 运行态留在 `~/.codex/`；除非用户明确要求安装/同步配置，不要从本仓库写回这些目录。
- 不读取或复制两边的 `history.jsonl`、`sessions/`、`file-history/`、`paste-cache/`、`shell-snapshots/`、SQLite 日志、credentials/auth 文件。
- 项目级可共享证据只放在项目根：`audit/`、`delivery/proof.json`、`delivery/goal_proof.md`、`report_claims.tsv`、`numeric_reference.tsv`、`.bio_harness/logs/`。
- 审核和验收只比较这些共享证据与源数据/脚本，不用某个 agent 的聊天记录或缓存作为事实来源。
- 如果两边结论冲突，以 harness 退出码、`audit.json`、`proof.json`、源表复算结果为准。

### 写入隔离与审核独立（防并发污染）

同一项目、同一时刻，按以下分工，避免两个 agent 互相踩写、或污染审计独立性：

- **单一 writer**：同一项目根下任一时刻只允许一个 agent 写入（跑分析、改 `results/`/`scripts/`/`reports/`/`delivery/`、跑 `package`/`collect`/`proof finalize`/`gate`）。开写前先取 `.bio_harness/.lock`（见下）；取不到就等待或转为只读审核，不要并发写同一棵树。
- **审核/验收方默认只读**：做 review/审核/验收的 agent 对交付物**只读**，只允许写 `audit/`（`audit.json` 等审计发现）或独立的 review 输出；**发现问题只标记、不顺手修**交付物——修复交回写入方，保持审计独立。
- **验收审冻结快照**：验收必须针对**已提交的快照**，不审正在变化的工作树。开审前 `git status` 确认无未提交改动，并核对 `delivery/proof.json` 的 `git_commit`、`plan_sha256` 等于当前 checkout 的 commit 与 `plan.md`；不一致就拒绝验收，要求写入方先提交冻结。
- **审计文件用共享标准（防"各写各的、不是一个事儿"）**：两个 agent 的审计发现写成 `audit/<module>.<agent>.md`（`agent ∈ {claude, codex}`；`module` 用 `plan.md` 任务名**逐字**；文件头记 `audited_commit`），各写各的文件、绝不互踩。完整格式与"不一致谁说了算"见 [`docs/SHARED-AUDIT.md`](docs/SHARED-AUDIT.md)；机器核对两边是否审同一版：`python3 harness/lib/audit_reconcile.py <项目根>`。

### `.bio_harness/.lock` 写锁约定（轻量、咨询式）

- 位置：项目根 `.bio_harness/.lock`，属运行态，**不入库**、不当共享证据。
- 内容：持锁 agent 名、pid、主机、ISO 时间戳；陈旧阈值默认 30 分钟（`BIO_LOCK_TTL` 秒可调）。
- 用 `harness/lib/agent_lock.sh` 取/查/放：

```bash
HARNESS_ROOT="$(sh harness/lib/resolve_harness.sh . 2>/dev/null || true)"
sh "$HARNESS_ROOT/lib/agent_lock.sh" acquire claude .   # 写前取锁，被占用则非零退出
sh "$HARNESS_ROOT/lib/agent_lock.sh" status .
sh "$HARNESS_ROOT/lib/agent_lock.sh" release claude .   # 写完释放（长写入应周期性重新 acquire 刷新）
```

- 咨询式：当前靠各 agent 自觉先 `acquire`；陈旧锁可 `acquire --force` 打破并记录。
- **把锁检查接进 `proof.py` / `gate` 使之强制，是后续项**——本次只立约定 + 提供工具，不改 proof/gate。

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
