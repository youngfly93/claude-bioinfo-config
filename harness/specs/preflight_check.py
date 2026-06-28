#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "quality"))
from common import Issue, exit_code_for, find_plan, find_sample_sheet, first_existing, has_any, print_issues, project_root, read_text, simple_yaml_value


def lint_sample_sheet(path: Path) -> list[Issue]:
    issues: list[Issue] = []
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
        issues.append(Issue("P1", "SAMPLE_ID_MISSING", "样本表缺少 sample_id/sample/id 列", str(path)))
    if not group_col:
        issues.append(Issue("P1", "GROUP_MISSING", "样本表缺少 group/condition/分组 列", str(path)))
    if sample_col:
        seen: dict[str, int] = {}
        for idx, row in enumerate(rows, start=2):
            sid = (row.get(sample_col) or "").strip()
            if not sid:
                issues.append(Issue("P1", "SAMPLE_ID_EMPTY", f"第 {idx} 行 sample_id 为空", str(path)))
            if sid in seen:
                issues.append(Issue("P1", "SAMPLE_ID_DUP", f"样本 ID 重复：{sid}，首次出现于第 {seen[sid]} 行", str(path)))
            seen[sid] = idx
    if group_col:
        groups = sorted({(r.get(group_col) or "").strip() for r in rows if (r.get(group_col) or "").strip()})
        if len(groups) < 2:
            issues.append(Issue("P1", "GROUP_LEVEL_LT2", f"分组水平少于 2 个：{groups}", str(path)))
    return issues


def run(root: Path) -> list[Issue]:
    issues: list[Issue] = []

    plan = find_plan(root)
    if not plan:
        issues.append(Issue("P0", "PLAN_MISSING", "缺少 plan.md/计划.md；不能启动生信交付 goal loop", str(root), "先运行 bio-project-init/bio-grill 建立分析计划"))
    else:
        text = read_text(plan)
        if not has_any(text, [r"contrast", r"对比", r"分组", r"group"]):
            issues.append(Issue("P2", "PLAN_CONTRAST_UNCLEAR", "plan.md 未明确分组/contrast 方向", str(plan)))
        if not has_any(text, [r"FDR", r"padj", r"p\.adjust", r"p[- ]?value", r"阈值", r"log2FC"]):
            issues.append(Issue("P2", "PLAN_THRESHOLD_UNCLEAR", "plan.md 未明确统计阈值或判定标准", str(plan)))
        if not has_any(text, [r"GRCh", r"GRCm", r"genome", r"reference", r"annotation", r"GENCODE", r"Ensembl", r"数据库", r"版本"]):
            issues.append(Issue("P2", "PLAN_REFERENCE_UNCLEAR", "plan.md 未明确参考基因组/注释/数据库版本", str(plan)))

    contract = first_existing(root, ["contract.yaml", "project_contract.yaml"])
    if not contract:
        issues.append(Issue("P3", "CONTRACT_MISSING", "缺少 contract.yaml；建议把客户合同、分析合同、验收条件结构化", str(root)))
    else:
        ctext = read_text(contract)
        for key in ["assay", "organism", "deliverable_type"]:
            if simple_yaml_value(ctext, key) is None:
                issues.append(Issue("P2", f"CONTRACT_{key.upper()}_MISSING", f"contract.yaml 缺少 {key}", str(contract)))
        if "contrasts:" not in ctext:
            issues.append(Issue("P1", "CONTRACT_CONTRASTS_MISSING", "contract.yaml 缺少 contrasts 段，无法确认比较方向", str(contract)))

    manifest = first_existing(root, ["data_manifest.yaml", "metadata/data_manifest.yaml"])
    manifest_text = read_text(manifest) if manifest else ""
    if not manifest:
        issues.append(Issue("P3", "DATA_MANIFEST_MISSING", "缺少 data_manifest.yaml；建议登记输入文件、样本表、MD5、来源", str(root)))

    sample_sheet = find_sample_sheet(root, manifest_text)
    if sample_sheet:
        issues.extend(lint_sample_sheet(sample_sheet))
    else:
        issues.append(Issue("P3", "SAMPLE_SHEET_MISSING", "未找到 sample_sheet.tsv/csv；若项目有样本，必须登记样本表", str(root)))

    ref_lock = first_existing(root, ["reference.lock", "metadata/reference.lock"])
    if not ref_lock:
        issues.append(Issue("P3", "REFERENCE_LOCK_MISSING", "缺少 reference.lock；报告中的参考版本将难以追溯", str(root)))
    else:
        rtext = read_text(ref_lock)
        if not has_any(rtext, [r"genome_build\s*[:=]", r"GRCh", r"GRCm"]):
            issues.append(Issue("P2", "REFERENCE_BUILD_MISSING", "reference.lock 未记录 genome_build", str(ref_lock)))
        if not has_any(rtext, [r"annotation\s*[:=]", r"GENCODE", r"Ensembl", r"RefSeq"]):
            issues.append(Issue("P2", "REFERENCE_ANNOTATION_MISSING", "reference.lock 未记录 annotation/database 版本", str(ref_lock)))

    return issues


def main() -> int:
    ap = argparse.ArgumentParser(description="Bioinformatics delivery preflight check")
    ap.add_argument("project", nargs="?", default=".")
    ap.add_argument("--strict", action="store_true", help="P2 warnings also fail")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    issues = run(project_root(args.project))
    print_issues(issues, as_json=args.json)
    return exit_code_for(issues, strict=args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
