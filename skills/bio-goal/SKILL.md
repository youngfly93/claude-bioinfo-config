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

## 用法：一条命令生成完成条件（**别在本 skill 里重述检查链**）

完成条件（proof 命令链 + exit0 + 交付物清单 + finalize 强校验 + stop 条件）的**单一真源是 `bio_goal.sh`**——它打印绝对路径、插件安装/任意 cwd 都能跑。本 skill **只负责定位 harness 并调用它、把输出原样交给 `/goal`**，绝不把命令链抄一遍（抄了就会和脚本漂移——改脚本忘改这里）。

```bash
HARNESS_ROOT="$(sh harness/lib/resolve_harness.sh . 2>/dev/null || sh "${CLAUDE_PLUGIN_ROOT}/harness/lib/resolve_harness.sh" .)"
sh "$HARNESS_ROOT/bin/bio_goal.sh" .      # 打印 /goal 完成条件（proof 链 + 全 exit0 + finalize 强校验 + stop）
```

把上面输出的**完成条件整段**交给 Claude Code 的 `/goal`。要点（都由脚本输出承载，此处只作导读、不重述命令）：

- 所有命令 `exit_code=0`；P0/P1 必须修复后重跑；只剩 P2/P3 → 写 proof `open_warnings`，可 `PASS_WITH_WARN`。
- final status 由 `proof.py finalize` **强校验**后给出（必需命令齐、全 exit0、有 zip、有 `audit/audit.json`，否则拒绝并置 FAIL——人工填不进去）；自动化自检 `proof.py status --require-pass .`。
- 若长时间不能收敛，停止并输出 blocker + 当前 proof 状态 + 最小下一步。

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
