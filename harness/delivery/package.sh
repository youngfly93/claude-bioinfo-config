#!/usr/bin/env sh
set -eu
# 去重：复用 bio-deliver 单一真源 zip_pack.py（项目名_交付_YYYYMMDD.zip 同名同位）
BIO="${CLAUDE_PLUGIN_ROOT:-$HOME/.claude}/skills/bio-deliver/scripts"
exec python3 "$BIO/zip_pack.py" "$@"
