#!/usr/bin/env sh
# Print a Claude Code /goal completion condition for a bioinformatics delivery project.
set -eu
PROJECT_DIR="${1:-.}"
cat <<EOF
请开启 /goal，并持续推进当前生信交付项目，直到以下完成条件全部满足。不要用主观判断代替 harness 证明。

完成条件：

1. 使用 proof wrapper 执行并记录所有命令，命令、退出码、stdout/stderr 日志路径必须进入 delivery/proof.json 和 goal_proof.md：

   python3 harness/delivery/proof.py init ${PROJECT_DIR}
   python3 harness/delivery/proof.py run --name preflight ${PROJECT_DIR} -- bash harness/specs/preflight_check.sh ${PROJECT_DIR}
   python3 harness/delivery/proof.py run --name validate_strict ${PROJECT_DIR} -- bash harness/quality/validate.sh --strict ${PROJECT_DIR}
   python3 harness/delivery/proof.py run --name audit ${PROJECT_DIR} -- bash harness/quality/run_audit.sh ${PROJECT_DIR}
   python3 harness/delivery/proof.py run --name ai_scan ${PROJECT_DIR} -- bash harness/delivery/ai_scan.sh ${PROJECT_DIR}
   python3 harness/delivery/proof.py run --name package ${PROJECT_DIR} -- bash harness/delivery/package.sh pack ${PROJECT_DIR}/delivery

2. 所有命令退出码为 0。若存在 P0/P1，必须先修复再继续；若只有 P2/P3，记录在 proof 的 open_warnings 中。

3. 交付目录至少包含：
   - final report 或交付说明
   - figures/tables 或等价主题目录
   - report_claims.tsv 或 numeric_reference.tsv
   - audit/audit.json
   - delivery/proof.json
   - delivery/goal_proof.md
   - zip 包与 md5

4. delivery/proof.json 的 status 必须是 PASS 或 PASS_WITH_WARN；goal_proof.md 必须可读地列出：plan hash、git commit、harness version、命令清单、退出码、artifact 路径、md5、未解决 warning。

5. 若连续 10 个 turn 仍不能满足完成条件，停止循环，输出 blocker 列表、当前 proof 状态和下一步最小修复建议。
EOF
