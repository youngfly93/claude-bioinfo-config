---
name: bio-handoff
description: >-
  生信分析/审批的「交接棒」——在短上下文里干有界的活，把在制状态写进项目根的 HANDOFF.md，
  让 /clear、/compact 或换会话之后能原样接上，不出现分析断层、审核口径不一。
  两个动作：写交接棒（阶段交界/清理前）、读交接棒（接手/审批时按协议再入水）。
  触发条件：用户说"交接"、"handoff"、"hand off"、"存档继续"、"clear 前保存"、"compact 前先记"、
  "接手继续"、"续上"、"换个上下文接着干"、"这个分析先封存"。
  不适用于：新建项目脚手架（用 bio-project-init）、不熟项目从零建图（用 bio-zoom-out）、
  只想快速 compact 记 todo（用 /save）。
---

# 生信分析/审批 交接棒

长上下文里分析质量会掉（注意力稀释、中段遗忘、决策漂移）。解法不是撑大 context 或指望 compact，而是：

> **文件是真源，context 是耗材。** 读账本 → 干一段有界的活 → 写回账本 → 交棒。

本 skill 维护项目根的一份**小** `HANDOFF.md`——它是**当前状态的快照**（可覆盖、保持精简），不是流水账（流水账是 `execution_log.md`，append-only）。

## 写交接棒（WRITE）

**时机**：阶段交界、`/clear`/`/compact` 前、要换会话/换人接手、用户说"交接/封存"。

把当前在制状态蒸馏进 `HANDOFF.md`（**索引不复制**——数字/决策留在各自真源文件，这里只给指针）：

```markdown
# HANDOFF · <项目名>  (更新: <绝对日期>)

## 现在在做什么
<一句话：当前阶段目标>

## 已完成（每条带证据路径，做完的压成一行）
- <如：差异表达 → results/03_deg/deg_tumor_vs_normal.tsv>

## 进行中 / 下一步（精确到动作）
- <如：下一步跑 scripts/04_enrich.R；输入 deg.tsv；卡在 KEGG 物种参数未定>

## 已锁决策 & 审核口径（合同 —— 审批每次只认这段）
- 阈值：FDR<0.05 · |logFC|≥1 · <其它>
- 参考：基因组 hg38 / Gencode vNN · 数据库版本
- contrast / 分组定义：<...>
- "算完成"的定义、必交付物清单：<...>

## 待决 / 卡点
- <开放问题、在等用户确认的点>

## 复盘指针（接手按序读）
1. plan.md（设计与需求真源）
2. 本文件（在制状态）
3. numeric_reference.tsv / report_claims.tsv（数字真源）
4. audit/*.md · fix_log.md（审计/修复进展）
5. docs/analysis-decisions/（已落档的关键决策）
```

**两条铁律**：
- **必须小**：它是"索引 + 当前指针"。把 context 倒进文件只是把膨胀问题搬个地方——做完的条目压成一行，过期的删。
- **不另立真源**：阈值/数字/决策仍以 `plan.md`、`numeric_reference.tsv`、`analysis-decisions/` 为准；`HANDOFF.md` 只指过去，冲突时以真源为准并就地更正。

## 读交接棒 / 续接（READ）

**时机**：开会话、`/compact` 后、接手继续、进入审批。

**再入水协议**（别凭残留 context 硬接）：
1. 先读 `HANDOFF.md` 的「现在在做什么 / 下一步 / 待决」——3 句话内重建坐标。
2. 按「复盘指针」顺序补读真源文件，确认与快照一致（不一致以真源为准，并更正 HANDOFF）。
3. 复述一句"我接的是 X，下一步做 Y，口径是 Z"给用户确认，再动手。
4. 项目不熟、快照不足以接上 → 转 `bio-zoom-out` 先建图，再回来续接。

## 审批专用：fresh context + 只读口径合同

最终审批/审核**最好在干净的新上下文里做**，只读「**审核口径合同段 + 结果文件 + 数字台账(report_claims/numeric_reference)**」：
- **新鲜** → 不被分析阶段那段已退化的长 context 拖累，质量高。
- **独立** → 分析时那个有偏的 context 不参与评审，口径只认合同段（每次一致）。
- 与 `bio-result-audit` / `bio-audit-fanout` 一条线：审批就是"fresh 子代理按合同复核"，承重结论默认证伪。

## 与其他 skill 的关系

- `/save`：通用快速 compact 记 todo；本 skill 是**结构化、生信专用、含审核口径合同**的交接，二者可叠用。
- `bio-project-init`：建项目时可顺手生成空 `HANDOFF.md`；`execution_log.md`（流水账）与 `HANDOFF.md`（当前快照）分工不混。
- `bio-zoom-out`：从零重建项目地图；本 skill 是接续**在制状态**。快照不够时退回 zoom-out。

## 纪律

- 写之前先确认在正本目录（别把 HANDOFF 写进副本/旧版本目录）。
- 快照只记**能溯源**的状态，不杜撰进度；拿不准的进度标"待核"。
- 接手第一动作永远是"读 HANDOFF + 复述确认"，不是直接改文件。
- HANDOFF 与真源冲突 → 以真源为准，就地更正快照，并向用户点明。
