#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

from common import Issue, SEVERITY_RANK, exit_code_for, print_issues, project_root

CHECKS = [
    ("preflight", "../specs/preflight_check.py"),
    ("sample_sheet", "sample_sheet_lint.py"),
    ("contrast", "contrast_lint.py"),
    ("reference_lock", "reference_lock_check.py"),
    ("report_claims", "report_claims_check.py"),
    ("numeric_reference", "numeric_reference_verify.py"),
    ("figure_spec", "figure_spec_check.py"),
    ("limitation", "limitation_register.py"),
]


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(root: Path) -> list[Issue]:
    issues: list[Issue] = []
    here = Path(__file__).resolve().parent
    for name, rel in CHECKS:
        path = (here / rel).resolve()
        try:
            mod = load_module(path)
            issues.extend(mod.run(root))
        except Exception as e:
            issues.append(Issue("P1", f"CHECK_{name.upper()}_ERROR", f"检查器运行失败：{e}", str(path)))
    # de-duplicate exact issues when preflight and specific lint both report the same thing
    unique = []
    seen = set()
    for i in issues:
        key = (i.severity, i.code, i.message, i.path)
        if key not in seen:
            seen.add(key)
            unique.append(i)
    return sorted(unique, key=lambda x: SEVERITY_RANK.get(x.severity, 9))


def main() -> int:
    ap = argparse.ArgumentParser(description="Run deterministic bioinformatics delivery validation")
    ap.add_argument("project", nargs="?", default=".")
    ap.add_argument("--strict", action="store_true", help="P2 warnings also fail")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    issues = run(project_root(args.project))
    print_issues(issues, args.json)
    return exit_code_for(issues, args.strict)

if __name__ == "__main__":
    raise SystemExit(main())
