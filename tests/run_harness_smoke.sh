#!/usr/bin/env sh
# 端到端 smoke：在最小 fixture 上跑完整 bio-goal proof 链（全部命令进 proof + collect + 强校验 finalize）。
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)"
H="$ROOT/harness"

# 关键词别撞生信术语：ai_trace_scan 自检（基因 GPT2/GEMINI 不报、真 AI 照报）
python3 "$ROOT/skills/bio-deliver/scripts/ai_trace_scan.py" selftest

TMP="${TMPDIR:-/tmp}/bio_harness_smoke_$$"
trap 'rm -rf "$TMP"' EXIT
cp -R "$ROOT/tests/fixtures/minimal_project" "$TMP"
cd "$TMP"

python3 "$H/delivery/proof.py" init .
python3 "$H/delivery/proof.py" run --name preflight . -- bash "$H/specs/preflight_check.sh" .
python3 "$H/delivery/proof.py" run --name validate_strict . -- bash "$H/quality/validate.sh" --strict .
python3 "$H/delivery/proof.py" run --name audit . -- bash "$H/quality/run_audit.sh" .
python3 "$H/delivery/proof.py" run --name ai_scan . -- bash "$H/delivery/ai_scan.sh" .
python3 "$H/delivery/proof.py" run --name privacy_scan . -- python3 "$H/delivery/privacy_scan.py" "$TMP/delivery"
python3 "$H/delivery/proof.py" run --name structure_check . -- python3 "$H/delivery/structure_check.py" "$TMP/delivery"
python3 "$H/delivery/proof.py" run --name dedup_check . -- python3 "$H/delivery/dedup_check.py" "$TMP/delivery"
python3 "$H/delivery/proof.py" run --name package . -- bash "$H/delivery/package.sh" pack "$TMP/delivery" minimal_project
python3 "$H/delivery/proof.py" collect .
python3 "$H/delivery/proof.py" finalize . --status PASS
python3 "$H/delivery/proof.py" status --require-pass .
python3 "$ROOT/hooks/delivery_gate.py" </dev/null

# skill 契约 lint：name==目录、公开 skill 不读运行态历史（把 habit-analyzer 那类隐私违规焊死）
python3 "$ROOT/tests/test_skill_contracts.py"

# 负向：坏案例 fixture——故意植入缺陷，门必须拦住（把 known_issues 高频错变成可执行保证）
python3 "$ROOT/tests/run_badcase_fixtures.py"

echo "bio harness smoke: PASS"
