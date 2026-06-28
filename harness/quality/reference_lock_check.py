#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from common import Issue, exit_code_for, first_existing, has_any, print_issues, project_root, read_text


def run(root: Path) -> list[Issue]:
    path = first_existing(root, ["reference.lock", "metadata/reference.lock"])
    if not path:
        return [Issue("P3", "REFERENCE_LOCK_MISSING", "缺少 reference.lock", str(root))]
    text = read_text(path)
    issues: list[Issue] = []
    checks = {
        "organism": [r"organism\s*[:=]", r"Homo sapiens", r"Mus musculus"],
        "genome_build": [r"genome_build\s*[:=]", r"GRCh\d+", r"GRCm\d+"],
        "annotation": [r"annotation\s*[:=]", r"GENCODE", r"Ensembl", r"RefSeq"],
        "created_at": [r"created_at\s*[:=]", r"date\s*[:=]"],
    }
    for key, patterns in checks.items():
        if not has_any(text, patterns):
            issues.append(Issue("P2", f"REFERENCE_{key.upper()}_MISSING", f"reference.lock 未记录 {key}", str(path)))
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
