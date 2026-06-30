#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from common import Issue, exit_code_for, first_existing, print_issues, project_root

REQUIRED = ["claim_id", "claim", "value", "source_file", "source_column"]


def _numeric(s):
    try:
        return float(str(s).strip())
    except (ValueError, TypeError):
        return None


def _reconcile_value(root: Path, row: dict, idx: int, path: Path, issues: list) -> None:
    """把承重数字与源表单元格对账——堵 known_issues #1（报告数值≠源数据，P0）。
    保守：只对【纯数字 value + .tsv/.csv 源 + 指定列】对账，其余跳过（避免文本误报）。"""
    value = (row.get("value") or "").strip()
    sf = (row.get("source_file") or "").strip()
    sc = (row.get("source_column") or "").strip()
    if not (value and sf and sc) or _numeric(value) is None:
        return                                   # 缺字段或文本 value：不在此对账
    src = root / sf
    if not src.exists():
        src = Path(sf)
    if not src.exists() or src.suffix.lower() not in (".tsv", ".csv"):
        return                                   # 源缺失已由 SOURCE_MISSING 覆盖；非表格源跳过
    delim = "\t" if src.suffix.lower() == ".tsv" else ","
    try:
        with src.open(newline="", encoding="utf-8-sig") as f:
            srows = list(csv.DictReader(f, delimiter=delim))
    except Exception:
        return
    if not srows:
        return
    if sc not in (srows[0].keys() or []):
        issues.append(Issue("P1", "REPORT_CLAIM_SOURCE_COLUMN_NOT_FOUND",
                            f"第 {idx} 行 source_column '{sc}' 不在 {sf} 表头", str(path)))
        return
    vnum = _numeric(value)
    cells = [(r.get(sc) or "").strip() for r in srows]
    matched = value in cells or any(_numeric(c) == vnum for c in cells if _numeric(c) is not None)
    if not matched:
        issues.append(Issue("P1", "REPORT_CLAIM_VALUE_NOT_IN_SOURCE",
                            f"第 {idx} 行 value={value} 在源 {sf} 列 '{sc}' 中找不到——数值与源数据不一致？",
                            str(path)))


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
        _reconcile_value(root, row, idx, path, issues)
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
