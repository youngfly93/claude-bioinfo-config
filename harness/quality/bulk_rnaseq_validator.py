#!/usr/bin/env python3
"""bulk RNA-seq 方法学 gate：机器早拦外包最常翻车的几类(分组/重复/contrast 方向/阈值/gene id)。
输入缺失=P3 建议(不强制那层)；输入在但有问题=P1/P2。stdlib only。"""
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from common import (Issue, exit_code_for, find_plan, find_sample_sheet,
                    first_existing, has_any, print_issues, project_root, read_text)


def run(root: Path) -> list[Issue]:
    issues: list[Issue] = []
    plan = find_plan(root)
    ref = first_existing(root, ["reference.lock"])
    contract = first_existing(root, ["contract.yaml"])
    src = " ".join(read_text(p) for p in (plan, ref, contract) if p)

    # 1. 样本表 / 分组 / 重复
    ss = find_sample_sheet(root)
    if not ss:
        issues.append(Issue("P3", "RNASEQ_SAMPLE_SHEET_MISSING", "未见 sample_sheet（建议登记样本/分组/批次）", str(root)))
    else:
        delim = "\t" if ss.suffix == ".tsv" else ","
        rows = [r for r in csv.reader(read_text(ss).splitlines(), delimiter=delim) if r]
        if rows:
            header = [h.strip().lower() for h in rows[0]]
            gcols = [i for i, h in enumerate(header) if h in ("group", "condition", "分组", "组别")]
            if not gcols:
                issues.append(Issue("P1", "RNASEQ_NO_GROUP_COL", "sample_sheet 无 group/condition 列，无法确认分组", str(ss)))
            else:
                gi = gcols[0]
                cnt = Counter(r[gi].strip() for r in rows[1:] if len(r) > gi and r[gi].strip())
                if len(cnt) < 2:
                    issues.append(Issue("P1", "RNASEQ_LT2_GROUPS", f"分组数 <2：{dict(cnt)}", str(ss)))
                small = {g: n for g, n in cnt.items() if n < 2}
                if small:
                    issues.append(Issue("P1", "RNASEQ_NO_REPLICATE", f"以下组无生物学重复(n<2)：{small}", str(ss)))

    # 2. contrast 方向
    ct = first_existing(root, ["contrasts.tsv", "metadata/contrasts.tsv"])
    if ct:
        head = (read_text(ct).splitlines() or [""])[0].lower()
        if not (("numerator" in head and "denominator" in head) or "vs" in head):
            issues.append(Issue("P1", "RNASEQ_CONTRAST_DIR_AMBIG",
                                "contrasts.tsv 未明确方向(应含 numerator/denominator 或 A_vs_B)", str(ct)))
    elif not has_any(src, [r"\bvs\b", r"对照", r"contrast", r"numerator"]):
        issues.append(Issue("P3", "RNASEQ_CONTRAST_UNDEFINED", "未见 contrasts.tsv，plan 也未写明 contrast 方向", str(root)))

    # 3. 阈值
    if not has_any(src, [r"FDR", r"padj", r"q.?value", r"adj\.?\s*P"]):
        issues.append(Issue("P2", "RNASEQ_FDR_THRESHOLD_MISSING", "未声明多重检验阈值(FDR/padj)", str(plan or root)))
    if not has_any(src, [r"log2?\s*FC", r"fold.?change", r"logFC"]):
        issues.append(Issue("P2", "RNASEQ_LOGFC_THRESHOLD_MISSING", "未声明 logFC 阈值", str(plan or root)))

    # 4. gene id 类型
    if not has_any(src, [r"Ensembl", r"ENSG", r"Entrez", r"Symbol", r"gene.?id", r"基因\s*ID"]):
        issues.append(Issue("P3", "RNASEQ_GENE_ID_TYPE_UNSTATED", "未说明 gene id 类型(Ensembl/Entrez/Symbol)", str(plan or root)))
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
