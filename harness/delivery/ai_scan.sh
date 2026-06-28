#!/usr/bin/env sh
set -eu
# 去重：复用 bio-deliver 单一真源 ai_trace_scan.py（不维护第二套 AI 扫描）
BIO="${CLAUDE_PLUGIN_ROOT:-$HOME/.claude}/skills/bio-deliver/scripts"
exec python3 "$BIO/ai_trace_scan.py" scan "$@"
