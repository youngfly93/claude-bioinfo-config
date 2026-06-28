#!/usr/bin/env sh
# Print a Claude Code /goal completion condition for a bioinformatics delivery project.
# 输出绝对路径，因此无论 harness 在项目内、插件目录还是 ~/.claude，goal loop 都能跑。
set -eu
HARNESS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT_DIR="$(cd "${1:-.}" && pwd)"
PROJECT_NAME="$(basename "$PROJECT_DIR")"
P="python3 $HARNESS_ROOT/delivery/proof.py"
cat <<EOF
请开启 /goal，持续推进当前生信交付项目，直到以下完成条件全部满足。不要用主观判断代替 harness 证明。

完成条件：

1. 用 proof wrapper 执行并记录所有命令（命令/退出码/日志路径进 delivery/proof.json + goal_proof.md），并自动收集产物：

   $P init "$PROJECT_DIR"
   $P run --name preflight "$PROJECT_DIR" -- bash "$HARNESS_ROOT/specs/preflight_check.sh" "$PROJECT_DIR"
   $P run --name validate_strict "$PROJECT_DIR" -- bash "$HARNESS_ROOT/quality/validate.sh" --strict "$PROJECT_DIR"
   $P run --name audit "$PROJECT_DIR" -- bash "$HARNESS_ROOT/quality/run_audit.sh" "$PROJECT_DIR"
   $P run --name ai_scan "$PROJECT_DIR" -- bash "$HARNESS_ROOT/delivery/ai_scan.sh" "$PROJECT_DIR"
   $P run --name privacy_scan "$PROJECT_DIR" -- python3 "$HARNESS_ROOT/delivery/privacy_scan.py" "$PROJECT_DIR/delivery"
   $P run --name package "$PROJECT_DIR" -- bash "$HARNESS_ROOT/delivery/package.sh" pack "$PROJECT_DIR/delivery" "$PROJECT_NAME"
   $P collect "$PROJECT_DIR"

2. 所有命令退出码为 0。若存在 P0/P1，必须先修复再继续；若只有 P2/P3，记录在 proof 的 open_warnings 中。

3. 交付目录至少包含：final report 或交付说明；figures/tables 或等价主题目录；report_claims.tsv 或 numeric_reference.tsv；audit/audit.json；delivery/proof.json；delivery/goal_proof.md；zip 包（其 md5 记录在 proof.artifacts）。

4. 收尾（finalize 会强制校验：必需命令齐、全部 exit 0、有 zip 产物、有 audit/audit.json，否则拒绝 PASS 并置 FAIL）：

   $P finalize "$PROJECT_DIR" --status PASS
   仅 P2/P3 时：$P finalize "$PROJECT_DIR" --status PASS_WITH_WARN --warning "P2: ..."
   自动化自检（IN_PROGRESS 会返回 1）：$P status --require-pass "$PROJECT_DIR"

5. 若连续 10 个 turn 仍不能满足完成条件，停止循环，输出 blocker 列表、当前 proof 状态和下一步最小修复建议。
EOF
