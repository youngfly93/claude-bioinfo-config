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
- **结构/清爽也是审计维度**（除数字复算 §7 外）：两个 agent 都按 `skills/bio-result-audit/SKILL.md`「2.5 步骤地图 + 清爽体检」核——grep 脚本头四行契约重建 步骤→脚本→输入→输出 链、验路径合理性、揪孤儿/多余中间文件、查绘图是否现算。项目结构契约见 `AGENTS.md`「生信项目结构契约」。两边用同一套维度，才不会一个审结构一个不审。

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

## 7. 方法保真 + 理由核实（复算证不了的那一层——两边都必做）

> 加这节的由来：一轮 7 阶段复核里，数字全部零漂移、却仍漏判了"用假理由跳过 mandated 混合模型""主队列 432 样本被静默折进 unknown""graph pseudotime 从没跑却当图件缺"。根因——**数字复算只证"数字非造假"，证不了"方法对/严格完成"**：被偷换或跳过的方法会产出真实、可复现的数字，复算照样逐位对上。

所以除源表复算外，两个 agent 都要对每个 mandated 方法多判一层，写进各自 `.md` 的**方法保真表**：

| id | mandated 方法 | 实际 method_status | verdict | evidence |
|---|---|---|---|---|
| 04_scrna-07 | 4I-Tier3 `(1｜subject)` 混合模型 | `spearman_proxy_no_lme4_due_missing_subject_ids` | FALSE_REASON | stage4_..._mixed_models.tsv:2（该集实有 subject_id）|

方法保真条目的 `verdict` 在 CONFIRMED/REFUTED/UNSURE 之外，用四态：
- `FAITHFUL`（严格完成，方法=方案）
- `HONEST_BOUNDARY`（§12.2 诚实数据边界，有"试过撞墙"证据）
- `UNDISCLOSED_DOWNGRADE`（预注册方法被静默替换/跳过；P1/P2）
- `FALSE_REASON`（跳过的理由对该场景根本不成立；P1）

三条硬规则（漏判高发区，spec 锚定逐条、**不抽样**）：
1. **理由核实**：每个 `not_run/not_assessable/no_X_available/missing_X/blocked/skipped/fallback/deferred` 都是**待验证 claim 非事实**——到独立源头验 blocker 真伪（称"缺 subject_id"→ grep 源表；称"包缺失"→ 确认是否独立包而非找错命名空间）。对某数据集根本不成立 = `FALSE_REASON`/P1。
2. **raw-保真 > 自洽**：门控/映射必须回溯 **RAW 源字段**，拒**同源派生量自证**（`record_count==sample_count` 是同义反复、非 `metadata_match_rate`）；受控词表列（site/age/disease）查 **raw→mapped 折进率**抓静默坍缩。
3. **fallback 三分类**：缺失/降级分「**试过失败**(HONEST_BOUNDARY)/**从没试**(UNDISCLOSED_DOWNGRADE)/**授权延期**」——只有"试过撞墙"证据才算诚实边界。
4. **审移动靶要锁文件版本 + 别把"并发修复"误当"测量假象"**：审计一个**正在被 producer 主动修**的项目时，你的"前"测量与"后"测量可能落在**不同文件版本**上。**真实踩过（且连错两步）**：对抗式 agent 报 `site=unknown 661`（真缺陷）→ 我隔一段时间用另一方法得 `unknown=0` → 我误判成"朴素解析假象"、**撤回了这个真 finding**；实则 producer 在两次测量之间重生成了该文件、把 unknown 正确映射了（`master` mtime 变了、缺陷是被**修好**不是"从没存在"）。铁律：① 每次承重测量**记下文件 mtime/hash**，跨测量出现差异**先排除"文件被改/被修"再归因**，别默认是自己解析错、也别默认 finding 是假的；② 用第二种方法复核 finding 时确保**同一文件版本**（否则不是复核、是对比两个版本）；③ finding 与其 fix 都 pin 版本——移动靶上"消失的缺陷"要先分清是"被修好"还是"没测到"。
   （附：带引号/内嵌 JSON 的 TSV 复算仍**建议 `csv.reader`/pandas 而非裸 `split`/awk**、归一化比较用 `re.sub(r'[^a-z0-9]','',v.lower())`——好习惯；但**本例 awk 无辜**，版本错位别甩锅给解析。）

机器兜底（别只肉眼）：
```
python3 harness/quality/limitation_register.py <项目根>   # 抽全部 limitation 字符串，逐个要独立证据
python3 harness/quality/mapping_fidelity.py <tsv> --col site --raw-json-key regionre   # raw→mapped 折进率
```
