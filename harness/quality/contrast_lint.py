#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from common import Issue, exit_code_for, first_existing, print_issues, project_root, read_text


def run(root: Path) -> list[Issue]:
    contract = first_existing(root, ["contract.yaml", "project_contract.yaml"])
    if not contract:
        return [Issue("P3", "CONTRACT_MISSING", "缺少 contract.yaml，无法机器确认 contrast 方向", str(root))]
    text = read_text(contract)
    if "contrasts:" not in text:
        return [Issue("P1", "CONTRASTS_MISSING", "contract.yaml 缺少 contrasts 段", str(contract))]
    section = text.split("contrasts:", 1)[1]
    # Stop at the next top-level section if present.
    m = re.search(r"\n[A-Za-z_][A-Za-z0-9_]*:\s*\n", section)
    if m:
        section = section[:m.start()]
    blocks = re.split(r"\n\s*-\s+", "\n" + section)
    blocks = [b.strip() for b in blocks if b.strip()]
    issues: list[Issue] = []
    if not blocks:
        issues.append(Issue("P1", "CONTRASTS_EMPTY", "contrasts 段为空", str(contract)))
        return issues
    for idx, block in enumerate(blocks, start=1):
        for key in ["name", "numerator", "denominator"]:
            if not re.search(rf"(^|\n)\s*{key}\s*:\s*\S+", block):
                issues.append(Issue("P1", f"CONTRAST_{key.upper()}_MISSING", f"第 {idx} 个 contrast 缺少 {key}", str(contract)))
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
