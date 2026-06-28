#!/usr/bin/env python3
"""Common helpers for bioinformatics delivery harness checks.

Only uses Python stdlib so the harness can run on fresh macOS/Linux machines.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List, Optional

SEVERITY_RANK = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "INFO": 4}
FAIL_SEVERITIES = {"P0", "P1"}


@dataclass
class Issue:
    severity: str
    code: str
    message: str
    path: str = ""
    hint: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def project_root(arg: str | None = None) -> Path:
    return Path(arg or ".").expanduser().resolve()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def md5_file(path: Path) -> str:
    h = hashlib.md5()  # nosec: checksum for delivery integrity, not security auth
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def first_existing(root: Path, candidates: Iterable[str]) -> Optional[Path]:
    for c in candidates:
        p = root / c
        if p.exists():
            return p
    return None


def simple_yaml_value(text: str, key: str) -> Optional[str]:
    # Good enough for flat frontmatter/config fields without a PyYAML dependency.
    pat = re.compile(rf"^\s*{re.escape(key)}\s*:\s*(.+?)\s*$", re.M)
    m = pat.search(text)
    if not m:
        return None
    value = m.group(1).strip().strip('"\'')
    return value or None


def has_any(text: str, patterns: Iterable[str]) -> bool:
    return any(re.search(p, text, flags=re.I | re.M) for p in patterns)


def print_issues(issues: List[Issue], as_json: bool = False) -> None:
    if as_json:
        print(json.dumps([i.to_dict() for i in issues], ensure_ascii=False, indent=2))
        return
    if not issues:
        print("PASS: no issues")
        return
    print("| severity | code | path | message |")
    print("|---|---|---|---|")
    for i in sorted(issues, key=lambda x: SEVERITY_RANK.get(x.severity, 9)):
        path = i.path or "."
        msg = i.message.replace("|", "\\|")
        print(f"| {i.severity} | {i.code} | {path} | {msg} |")
        if i.hint:
            print(f"  hint: {i.hint}")


def exit_code_for(issues: List[Issue], strict: bool = False) -> int:
    fail = {"P0", "P1", "P2"} if strict else {"P0", "P1"}
    return 1 if any(i.severity in fail for i in issues) else 0


def git_commit(root: Path) -> str:
    try:
        cp = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=str(root),
            text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False
        )
        return cp.stdout.strip() or "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def find_plan(root: Path) -> Optional[Path]:
    return first_existing(root, ["plan.md", "计划.md", "analysis_plan.md"])


def find_sample_sheet(root: Path, manifest_text: str = "") -> Optional[Path]:
    m = re.search(r"^\s*sample_sheet\s*:\s*(.+?)\s*$", manifest_text, flags=re.M)
    candidates = []
    if m:
        candidates.append(m.group(1).strip().strip('"\''))
    candidates += [
        "metadata/sample_sheet.tsv", "metadata/samples.tsv", "sample_sheet.tsv",
        "samples.tsv", "metadata/sample_sheet.csv", "sample_sheet.csv",
    ]
    for c in candidates:
        p = root / c
        if p.exists():
            return p
    return None
