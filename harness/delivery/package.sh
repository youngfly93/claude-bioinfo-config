#!/usr/bin/env sh
set -eu
# 去重：复用 bio-deliver 单一真源 zip_pack.py（项目名_交付_YYYYMMDD.zip 同名同位）
# 脚本目录经共享解析器定位，插件安装 / ~/.claude / 仓库内直接跑 三种场景都可用。
SELF_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)"
BIO="$(sh "$SELF_DIR/../lib/resolve_bio_scripts.sh")" || exit 3
exec python3 "$BIO/zip_pack.py" "$@"
