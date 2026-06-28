#!/usr/bin/env sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)"
TMP="${TMPDIR:-/tmp}/bio_harness_smoke_$$"
trap 'rm -rf "$TMP"' EXIT
cp -R "$ROOT/tests/fixtures/minimal_project" "$TMP"
cd "$TMP"

bash "$ROOT/harness/specs/preflight_check.sh" .
bash "$ROOT/harness/quality/validate.sh" --strict .
bash "$ROOT/harness/quality/run_audit.sh" .
bash "$ROOT/harness/delivery/ai_scan.sh" .
python3 "$ROOT/harness/delivery/proof.py" init .
python3 "$ROOT/harness/delivery/proof.py" run --name preflight . -- bash "$ROOT/harness/specs/preflight_check.sh" .
bash "$ROOT/harness/delivery/package.sh" pack delivery minimal_project
python3 "$ROOT/harness/delivery/proof.py" artifact . "minimal_project_交付_$(date +%Y%m%d).zip"
python3 "$ROOT/harness/delivery/proof.py" finalize . --status PASS
python3 "$ROOT/hooks/delivery_gate.py"

echo "bio harness smoke: PASS"
