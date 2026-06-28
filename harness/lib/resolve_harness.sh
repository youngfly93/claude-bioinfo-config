#!/usr/bin/env sh
# Resolve the deterministic bioinformatics harness root.
# Usage:
#   HARNESS_ROOT="$(sh harness/lib/resolve_harness.sh [project_dir])"
# Candidate order intentionally prefers project-local harness, then plugin/global installs.

set -eu

is_harness_root() {
  [ -n "${1:-}" ] && [ -f "$1/specs/preflight_check.sh" ] && [ -f "$1/quality/validate.sh" ]
}

resolve_harness() {
  start="${1:-$PWD}"

  if [ -n "${HARNESS_BIO:-}" ] && is_harness_root "$HARNESS_BIO/harness"; then
    printf '%s\n' "$HARNESS_BIO/harness"
    return 0
  fi
  if [ -n "${HARNESS_BIO:-}" ] && is_harness_root "$HARNESS_BIO"; then
    printf '%s\n' "$HARNESS_BIO"
    return 0
  fi

  cur="$(cd "$start" 2>/dev/null && pwd -P || pwd -P)"
  while [ "$cur" != "/" ]; do
    if is_harness_root "$cur/harness"; then
      printf '%s\n' "$cur/harness"
      return 0
    fi
    cur="$(dirname "$cur")"
  done

  if [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && is_harness_root "$CLAUDE_PLUGIN_ROOT/harness"; then
    printf '%s\n' "$CLAUDE_PLUGIN_ROOT/harness"
    return 0
  fi

  for d in "$HOME/.claude/harness" "$HOME/.local/share/harness_bio/harness" "$HOME/.local/share/harness_bio"; do
    if is_harness_root "$d"; then
      printf '%s\n' "$d"
      return 0
    fi
  done

  return 1
}

resolve_harness "$@"
