#!/usr/bin/env sh
# Resolve the bio-deliver scripts dir (single source: ai_trace_scan.py / zip_pack.py).
# Usage:  BIO="$(sh harness/lib/resolve_bio_scripts.sh)"  || exit 3
# Candidate order mirrors resolve_harness.sh: env override → plugin root →
# repo-relative (this file lives at harness/lib/, scripts at skills/bio-deliver/scripts) → ~/.claude.
# The repo-relative fallback is what lets a fresh `git clone` (no plugin install,
# empty ~/.claude) still run tests/run_harness_smoke.sh — the repo's stated purpose.
set -eu

has_scripts() {
  [ -n "${1:-}" ] && [ -f "$1/ai_trace_scan.py" ] && [ -f "$1/zip_pack.py" ]
}

self_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)"

for cand in \
  "${BIO_DELIVER_SCRIPTS:-}" \
  "${CLAUDE_PLUGIN_ROOT:-}/skills/bio-deliver/scripts" \
  "$self_dir/../../skills/bio-deliver/scripts" \
  "$HOME/.claude/skills/bio-deliver/scripts" \
  "$HOME/.local/share/harness_bio/skills/bio-deliver/scripts"; do
  if has_scripts "$cand"; then
    printf '%s\n' "$(CDPATH= cd -- "$cand" && pwd -P)"
    exit 0
  fi
done

echo "resolve_bio_scripts.sh: cannot locate skills/bio-deliver/scripts (ai_trace_scan.py + zip_pack.py). Set BIO_DELIVER_SCRIPTS / CLAUDE_PLUGIN_ROOT, or install to ~/.claude." >&2
exit 1
