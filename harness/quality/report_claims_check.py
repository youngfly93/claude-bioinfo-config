#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from common import Issue, exit_code_for, first_existing, print_issues, project_root

REQUIRED = ["claim_id", "claim", "value", "source_file", "source_column"]


def has_report(root: Path) -> bool:
    for pat in ["*.docx", "*.pdf", "*.md", "reports/*.docx", "reports/*.pdf", "reports/*.md", "delivery/**/*.docx", "delivery/**/*.pdf"]:
        if any(root.glob(pat)):
            return True
    return False


def run(root: Path) -> list[Issue]:
    path = first_existing(root, ["report_claims.tsv", "audit/report_claims.tsv", "delivery/report_claims.tsv"])
    if not path:
        sev = "P1" if has_report(root) else "P2"
        return [Issue(sev, "REPORT_CLAIMS_MISSING", "缺少 report_claims.tsv；报告承重数字无法溯源", str(root))]
    issues: list[Issue] = []
    try:
        with path.open(newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f, delimiter="\t"))
    except Exception as e:
        return [Issue("P1", "REPORT_CLAIMS_READ_FAIL", f"report_claims.tsv 无法读取：{e}", str(path))]
    if not rows:
        return [Issue("P1", "REPORT_CLAIMS_EMPTY", "report_claims.tsv 为空", str(path))]
    cols = set(rows[0].keys() or [])
    for col in REQUIRED:
        if col not in cols:
            issues.append(Issue("P1", f"REPORT_CLAIMS_COL_{col.upper()}_MISSING", f"report_claims.tsv 缺少列：{col}", str(path)))
    for idx, row in enumerate(rows, start=2):
        for col in [c for c in REQUIRED if c in cols]:
            if not (row.get(col) or "").strip():
                issues.append(Issue("P1", f"REPORT_CLAIM_{col.upper()}_EMPTY", f"第 {idx} 行 {col} 为空", str(path)))
        sf = (row.get("source_file") or "").strip()
        if sf and not (root / sf).exists() and not Path(sf).exists():
            issues.append(Issue("P1", "REPORT_CLAIM_SOURCE_MISSING", f"第 {idx} 行 source_file 不存在：{sf}", str(path)))
        status = (row.get("status") or "").strip().upper()
        if "status" in cols and status and status not in {"VERIFIED", "CHECKED", "PASS", "OK"}:
            issues.append(Issue("P2", "REPORT_CLAIM_STATUS_NOT_VERIFIED", f"第 {idx} 行 status 不是 VERIFIED/PASS：{status}", str(path)))
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
