#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from common import Issue, exit_code_for, first_existing, print_issues, project_root

NUMERIC_RE = re.compile(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")


def run(root: Path) -> list[Issue]:
    path = first_existing(root, ["report_claims.tsv", "audit/report_claims.tsv", "delivery/report_claims.tsv"])
    if not path:
        return []
    issues: list[Issue] = []
    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    for idx, row in enumerate(rows, start=2):
        text = " ".join([(row.get("claim") or ""), (row.get("value") or "")])
        if NUMERIC_RE.search(text):
            if not (row.get("source_file") or "").strip():
                issues.append(Issue("P1", "NUMERIC_CLAIM_SOURCE_FILE_EMPTY", f"第 {idx} 行含数字但 source_file 为空", str(path)))
            if not (row.get("source_column") or "").strip():
                issues.append(Issue("P1", "NUMERIC_CLAIM_SOURCE_COLUMN_EMPTY", f"第 {idx} 行含数字但 source_column 为空", str(path)))
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
