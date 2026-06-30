# 双 agent 共享审计标准 (SHARED-AUDIT)

> 两个 agent（Claude / Codex）审同一个项目时，**文件与字段的单一标准**。
> 目的：根治"各写各的、最后发现说的不是一个事儿 / 两份混在一起"。
> 这是唯一真源——`AGENTS.md`、`CLAUDE.md`、`bio-result-auditor` 都指向本文件，不另立第二套。
>
> 前置纪律见 `AGENTS.md`「写入隔离与审核独立」：单一 writer、审核方只读、验收审冻结快照。
> 本文件只补它没说死的那三件：审同一版、用同一套模块名、写不撞的固定文件。

## 1. 审什么——同一个冻结快照（防"不是一个事儿"的根）

- 都审**已提交的 commit**，不审变化中的工作树。
- 开审前 `git status` 必须干净；核对 `delivery/proof.json` 的 `git_commit` == 当前 `HEAD`。
- 把审的 commit 短哈希写进审计文件头 `audited_commit:`——这是机器核对"两边是不是审了同一版"的唯一依据。**两边 commit 不同 = 当场就是两个事儿，别再往下比。**

## 2. 切成什么模块——用 plan.md 的任务名，逐字照抄

- 模块名 = `plan.md` 里的分析任务名，**两个 agent 逐字照用，不要各自意译**。
  （别一个叫 `DEG分析`、一个叫 `差异表达`——那就成两个事儿了。）
- `plan.md` 是模块词汇的单一真源；没有 plan.md 就先对齐出一份再审。

## 3. 写哪个文件——agent 限定、不撞、单写

- 文件名固定：**`audit/<module>.<agent>.md`**，`agent ∈ {claude, codex}`。
  例：`audit/02_deg.claude.md` 和 `audit/02_deg.codex.md`。
- 同一 `module` → 同一前缀 → 可直接并排 diff。
- **一个文件只有一个 writer**：你只写自己的 `.claude.md`，**绝不碰对方的 `.codex.md`**（反之亦然）。

## 4. 写成什么格式——固定文件头 + 固定字段

文件头（YAML frontmatter）：

```yaml
---
module: 02_deg            # = plan.md 任务名，逐字
agent: claude             # claude | codex
audited_commit: a1b2c3d   # git rev-parse --short HEAD
---
```

发现表（固定列，每条一个稳定 id）：

| id | severity | claim | evidence | verdict |
|---|---|---|---|---|
| 02_deg-01 | P1 | DEG 阈值与 plan.md 不一致 | scripts/03_deg.R:42 用 FDR<0.1，plan.md 要 0.05 | CONFIRMED |

- `id`：`<module>-NN`。**两边对同一条结论用同一 id** → 可按 id 对齐比对（一致/分歧一目了然）。
- `severity`：P0 / P1 / P2 / P3。
- `evidence`：必须是 `文件:行` 或 `表:列/单元格` 这种可复核的指针，不是散文。
- `verdict`：`CONFIRMED`（确证有问题）/ `REFUTED`（查后无问题）/ `UNSURE`（需人裁）。

## 5. 不一致了谁说了算

1. **能确定性核验的**（数字、文件存在、阈值、脚本行为）→ 跑脚本 / 源表复算**判死**，不靠观点。见 `AGENTS.md`：冲突以 harness 退出码、`audit.json`、`proof.json`、源表复算为准。
2. **真·方法学分歧**（没有确定性裁判）→ 人裁，且优先回 `bio-grill` 把上游 spec 钉死——频繁的 ② 往往是设计欠定义，两个模型各自填空。
3. 裁清楚的每一条 → **棘轮成 `known_issues` 或一个确定性 check**，下次不用再裁。频繁分歧会随棘轮自己变少。

## 6. 机器核对（别靠肉眼）

```
python3 harness/lib/audit_reconcile.py <项目根>
```

它检查：
- 每个 module 的 `claude`/`codex` 两份是否审了**同一个 commit**——不同就**响亮报错**（这就是"不是一个事儿"被当场抓住）；
- **覆盖缺口**：某 module 只有一边审了；
- 按 `id` 并排两边 `verdict`，标出 ✅一致 / ⚠️分歧，让人只盯真正要裁的那几条。
