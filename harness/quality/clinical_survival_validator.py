#!/usr/bin/env python3
"""临床/生存分析方法学 gate：查结局定义、删失编码、时间单位、cutpoint、PH 假设。
口径未写明=P2/P3 建议；数据驱动 cutpoint=过拟合提醒。stdlib only。"""
from __future__ import annotations

import argparse
from pathlib import Path
from common import (Issue, exit_code_for, find_plan, first_existing,
                    has_any, print_issues, project_root, read_text)

CHECKS = [
    ("SURV_OUTCOME_UNDEFINED", "P2", "未明确结局/事件变量(OS/PFS/DFS/event)",
     [r"\bOS\b", r"\bPFS\b", r"\bDFS\b", r"生存", r"结局", r"\bevent\b", r"vital.?status"]),
    ("SURV_CENSOR_UNDEFINED", "P2", "未说明删失编码(如 0=删失/1=事件)",
     [r"删失", r"censor", r"0\s*/\s*1", r"vital", r"deceased|alive"]),
    ("SURV_TIME_UNIT_UNDEFINED", "P3", "未说明随访时间单位(月/天/年)",
     [r"月", r"\b天\b", r"\b年\b", r"month", r"\bday", r"\byear", r"time.?unit"]),
    ("SURV_CUTPOINT_UNSTATED", "P2", "未说明连续变量分组 cutpoint(median? 数据驱动?)",
     [r"median", r"中位", r"cutoff", r"cutpoint", r"分位|quantile", r"high.*low|高.*低"]),
    ("SURV_PH_UNCHECKED", "P3", "未提 Cox 比例风险(PH)假设检验(cox.zph/Schoenfeld)",
     [r"\bPH\b", r"比例风险", r"proportional\s+hazard", r"cox\.zph", r"schoenfeld"]),
]


def run(root: Path) -> list[Issue]:
    plan = find_plan(root)
    contract = first_existing(root, ["contract.yaml"])
    src = " ".join(read_text(p) for p in (plan, contract) if p)
    if not src.strip():
        return [Issue("P3", "SURV_NO_PLAN", "未见 plan.md/contract，无法核对生存分析口径", str(root))]

    issues: list[Issue] = []
    for code, sev, msg, pats in CHECKS:
        if not has_any(src, pats):
            issues.append(Issue(sev, code, msg, str(plan or root)))
    # 数据驱动最优 cutpoint → 过拟合提醒
    if has_any(src, [r"最优\s*cut", r"optimal\s*cut", r"surv_cutpoint", r"maxstat"]):
        issues.append(Issue("P2", "SURV_DATADRIVEN_CUTPOINT",
                            "用了数据驱动最优 cutpoint —— 注意过拟合，须说明/独立验证", str(plan or root)))
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
