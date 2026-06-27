#!/usr/bin/env bash
# 一条命令把 pptx 渲染成预览 PNG，供逐页自查版式/留白/字体。
# 用法: bash preview.sh <deck.pptx> [输出目录] [dpi]
set -euo pipefail
PPTX="${1:?用法: preview.sh <deck.pptx> [outdir] [dpi]}"
OUTDIR="${2:-$(dirname "$PPTX")/_preview}"
DPI="${3:-100}"

SOFFICE="/Applications/LibreOffice.app/Contents/MacOS/soffice"
[ -x "$SOFFICE" ] || SOFFICE="$(command -v soffice || command -v libreoffice || true)"
[ -n "$SOFFICE" ] || { echo "需要 LibreOffice 渲染，未找到 soffice。"; exit 1; }

PY="$(command -v python3)"
mkdir -p "$OUTDIR"
TMPD="$(dirname "$PPTX")"
"$SOFFICE" --headless --convert-to pdf --outdir "$TMPD" "$PPTX" >/dev/null 2>&1
PDF="$TMPD/$(basename "${PPTX%.*}").pdf"

"$PY" - "$PDF" "$OUTDIR" "$DPI" <<'PYEOF'
import sys, fitz
pdf, outdir, dpi = sys.argv[1], sys.argv[2], int(sys.argv[3])
d = fitz.open(pdf)
for i in range(len(d)):
    d[i].get_pixmap(dpi=dpi).save(f"{outdir}/pg_{i+1:02d}.png")
print(f"✅ {len(d)} 页预览 → {outdir}/pg_*.png")
PYEOF
