---
name: bio-goal
description: 把生信外包项目放进可验证 goal loop：生成 /goal 完成条件，要求 preflight/validate/audit/AI扫描/打包/proof 全部通过。触发条件：用户说 goal loop、harness goal、持续执行直到交付、自动推进到可交付、bio-goal。
---

# bio-goal：生信交付 goal loop 入口

`bio-goal` 的职责不是直接分析数据，而是把当前项目转成 Claude Code `/goal` 能持续推进、且能被 harness 证明完成的目标。

核心原则：

- `/goal` 只负责外层持续推进；完成判断必须来自 harness 命令退出码和 proof artifacts。
- 不允许用“看起来完成了”“应该没问题”作为完成条件。
- 所有会影响交付的检查必须写入 `delivery/proof.json` 和 `delivery/goal_proof.md`。
- 若项目有 `spec.md`：它是 goal 的**人读完成清单**——goal 推进即逐条把 `[ ]` 做到 `[x]`（每条「验收:」证据在）。`spec.md` 全 `[x]` 与 harness proof PASS 必须一致，才算真完成；二者不符以 proof/证据为准。

## 先定位 harness

优先使用项目内 harness；否则使用插件内 harness：

```bash
HARNESS_ROOT="$(sh harness/lib/resolve_harness.sh . 2>/dev/null || sh ${CLAUDE_PLUGIN_ROOT}/harness/lib/resolve_harness.sh .)"
echo "$HARNESS_ROOT"
```

如果当前项目没有 harness，但插件目录有 harness，可以在命令中把 `harness/...` 替换为 `${HARNESS_ROOT}/...`。

## 推荐生成的 /goal 文案

让 Claude Code 开启 `/goal` 时，使用以下完成条件。根据项目路径把 `.` 替换成真实 project root。

```text
持续推进当前生信交付项目，直到以下条件全部满足，并且证明可见于 transcript、delivery/proof.json、delivery/goal_proof.md：

1. 执行并记录：
   python3 harness/delivery/proof.py init .
   python3 harness/delivery/proof.py run --name preflight . -- bash harness/specs/preflight_check.sh .
   python3 harness/delivery/proof.py run --name validate_strict . -- bash harness/quality/validate.sh --strict .
   python3 harness/delivery/proof.py run --name audit . -- bash harness/quality/run_audit.sh .
   python3 harness/delivery/proof.py run --name ai_scan . -- bash harness/delivery/ai_scan.sh .
   python3 harness/delivery/proof.py run --name privacy_scan . -- python3 harness/delivery/privacy_scan.py delivery
   python3 harness/delivery/proof.py run --name structure_check . -- python3 harness/delivery/structure_check.py delivery
   python3 harness/delivery/proof.py run --name package . -- bash harness/delivery/package.sh pack delivery
   python3 harness/delivery/proof.py collect .            # 自动把 zip 登记进 proof.artifacts

   （实际完成条件以 `bio_goal.sh` 输出为准——绝对路径，插件安装/任意 cwd 下都能跑。）

2. 所有命令 exit_code=0。若 P0/P1 存在，必须修复后重跑；若只有 P2/P3，写入 proof open_warnings，可最终 PASS_WITH_WARN。

3. 交付目录至少包含：报告或交付说明、图/表或主题目录、report_claims.tsv 或 numeric_reference.tsv、audit/audit.json、proof.json、goal_proof.md、zip 与 md5。

4. final status 必须是 PASS 或 PASS_WITH_WARN（finalize 会**强校验**：必需命令齐、全 exit 0、有 zip 产物、有 audit/audit.json，否则拒绝并置 FAIL——人工填不进去）：
   python3 harness/delivery/proof.py finalize . --status PASS
   或：python3 harness/delivery/proof.py finalize . --status PASS_WITH_WARN --warning "P2: ..."
   自动化自检：python3 harness/delivery/proof.py status --require-pass .   # IN_PROGRESS 返回 1

5. 若连续 10 个 turn 仍不能完成，停止并输出 blocker、当前 proof 状态、最小下一步修复。
```

## 与其它 bio-* skill 的关系 / 边界

- `bio-result-audit` / `bio-result-auditor`：负责**科学与数值审计**（数字台账、方法合理性）；本 harness 只做**确定性结构检查**，二者互补不重叠。
- `bio-deliver`：人工交付打包总入口。**去重**：harness 的 ai_scan / package 步骤已**复用** bio-deliver 的 `ai_trace_scan.py` / `zip_pack.py`，不另维护第二套；proof 由 `harness/delivery/proof.py` 记录退出码与产物 md5。
- `bio-handoff`：管上下文续接；`bio-goal` 管"可验证完成"。三者正交：handoff=不断层、goal=证明做完、deliver=打包发货。
- `bio-project-init` / `bio-grill`：补齐 plan / reference.lock、展开 `spec.md` 后进入 goal；goal 推进即逐条把 `spec.md` 的 `[ ]` 做到 `[x]`（验收证据在）。
- `bio-report`：写报告时必须维护 `report_claims.tsv`。

**可选规格（不强制那层）**：`contract.yaml` / `data_manifest.yaml` / `reference.lock` / `sample_sheet.tsv` 都是**可选**——缺失只记 P3 建议、不阻断 strict；一旦采用某文件，才强制其字段完整（P2）。真源仍是 `plan.md`。

## 禁止行为

- 禁止跳过 preflight/validate/audit/AI scan/package 任一阶段。
- 禁止在 P0/P1 未解决时打包。
- 禁止手写 proof 造假；proof 必须由 `harness/delivery/proof.py run` 记录命令退出码。
