#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from common import Issue, exit_code_for, git_commit, project_root
import validate


def summarize(issues: list[Issue]) -> dict[str, int]:
    counts = {"P0": 0, "P1": 0, "P2": 0, "P3": 0, "INFO": 0}
    for i in issues:
        counts[i.severity] = counts.get(i.severity, 0) + 1
    return counts


def main() -> int:
    ap = argparse.ArgumentParser(description="Create audit/audit.json from deterministic harness checks")
    ap.add_argument("project", nargs="?", default=".")
    ap.add_argument("--strict", action="store_true", help="Treat P2 as failing audit")
    args = ap.parse_args()
    root = project_root(args.project)
    issues = validate.run(root)
    counts = summarize(issues)
    status = "PASS" if counts.get("P0", 0) == 0 and counts.get("P1", 0) == 0 else "FAIL"
    if status == "PASS" and counts.get("P2", 0):
        status = "PASS_WITH_WARN"
    audit = {
        "schema_version": "bio-harness-audit.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_root": str(root),
        "git_commit": git_commit(root),
        "status": status,
        "summary": counts,
        "issues": [i.to_dict() for i in issues],
        "note": "Deterministic structural audit. Scientific/methodological judgment still belongs to bio-result-auditor or human reviewer.",
    }
    outdir = root / "audit"
    outdir.mkdir(exist_ok=True)
    out = outdir / "audit.json"
    out.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"audit_path": str(out), "status": status, "summary": counts}, ensure_ascii=False, indent=2))
    return exit_code_for(issues, strict=args.strict)

if __name__ == "__main__":
    raise SystemExit(main())
