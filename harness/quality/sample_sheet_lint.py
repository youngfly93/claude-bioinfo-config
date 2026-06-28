#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from common import Issue, exit_code_for, find_sample_sheet, first_existing, print_issues, project_root, read_text, simple_yaml_value


def run(root: Path) -> list[Issue]:
    issues: list[Issue] = []
    manifest = first_existing(root, ["data_manifest.yaml", "metadata/data_manifest.yaml"])
    manifest_text = read_text(manifest) if manifest else ""
    path = find_sample_sheet(root, manifest_text)
    if not path:
        return [Issue("P3", "SAMPLE_SHEET_MISSING", "未找到 sample_sheet.tsv/csv", str(root))]

    delim = "," if path.suffix.lower() == ".csv" else "\t"
    try:
        with path.open(newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f, delimiter=delim))
    except Exception as e:
        return [Issue("P1", "SAMPLE_SHEET_READ_FAIL", f"样本表无法读取：{e}", str(path))]
    if not rows:
        return [Issue("P1", "SAMPLE_SHEET_EMPTY", "样本表为空", str(path))]

    cols = set(rows[0].keys() or [])
    sample_col = next((c for c in ["sample_id", "sample", "SampleID", "Sample", "id"] if c in cols), None)
    group_col = next((c for c in ["group", "condition", "Group", "Condition", "分组"] if c in cols), None)
    if not sample_col:
        issues.append(Issue("P1", "SAMPLE_ID_MISSING", "缺少 sample_id/sample/id 列", str(path)))
    if not group_col:
        issues.append(Issue("P1", "GROUP_MISSING", "缺少 group/condition/分组 列", str(path)))

    seen: dict[str, int] = {}
    for idx, row in enumerate(rows, start=2):
        if sample_col:
            sid = (row.get(sample_col) or "").strip()
            if not sid:
                issues.append(Issue("P1", "SAMPLE_ID_EMPTY", f"第 {idx} 行 sample_id 为空", str(path)))
            elif sid in seen:
                issues.append(Issue("P1", "SAMPLE_ID_DUP", f"样本 ID 重复：{sid}", str(path), f"首次出现第 {seen[sid]} 行"))
            else:
                seen[sid] = idx
        if group_col and not (row.get(group_col) or "").strip():
            issues.append(Issue("P1", "GROUP_EMPTY", f"第 {idx} 行 group 为空", str(path)))

    if group_col:
        groups = sorted({(r.get(group_col) or "").strip() for r in rows if (r.get(group_col) or "").strip()})
        if len(groups) < 2:
            issues.append(Issue("P1", "GROUP_LEVEL_LT2", f"分组水平少于 2 个：{groups}", str(path)))

    contract = first_existing(root, ["contract.yaml", "project_contract.yaml"])
    if contract:
        ctext = read_text(contract)
        paired = (simple_yaml_value(ctext, "paired_design") or "").lower() in {"true", "yes", "1"}
        if paired and "pair_id" not in cols:
            issues.append(Issue("P1", "PAIR_ID_MISSING", "contract.yaml 标记 paired_design=true，但样本表缺少 pair_id", str(path)))
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
