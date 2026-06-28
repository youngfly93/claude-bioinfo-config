#!/usr/bin/env python3
from __future__ import annotations

import argparse
import struct
from pathlib import Path
from common import Issue, exit_code_for, print_issues, project_root

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".pdf", ".svg"}


def png_size(path: Path) -> tuple[int, int] | None:
    try:
        with path.open("rb") as f:
            sig = f.read(24)
        if sig.startswith(b"\x89PNG\r\n\x1a\n"):
            return struct.unpack(">II", sig[16:24])
    except Exception:
        return None
    return None


def run(root: Path) -> list[Issue]:
    issues: list[Issue] = []
    dirs = [p for p in [root / "figures", root / "plots", root / "delivery"] if p.exists()]
    files: list[Path] = []
    for d in dirs:
        files.extend([p for p in d.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXT])
    if not files:
        return [Issue("P3", "FIGURES_NOT_FOUND", "未找到 figures/plots/delivery 下的图件；若项目无图可忽略", str(root))]
    for p in files:
        if p.stat().st_size == 0:
            issues.append(Issue("P1", "FIGURE_EMPTY", "图件文件大小为 0", str(p)))
        if p.suffix.lower() == ".png":
            size = png_size(p)
            if size:
                w, h = size
                if w < 1200 or h < 900:
                    issues.append(Issue("P2", "FIGURE_LOW_PIXEL_SIZE", f"PNG 像素偏小：{w}x{h}", str(p), "客户报告通常建议 ≥1200x900；发表图需另按期刊规格"))
    return issues


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project", nargs="?", default=".")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    issues = run(project_root(args.project))
    print_issues(issues, args.json)
    return exit_code_for(issues, args.strict)

if __name__ == "__main__":
    raise SystemExit(main())
