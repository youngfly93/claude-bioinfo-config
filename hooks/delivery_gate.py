#!/usr/bin/env python3
"""Advisory/strict delivery gate for Claude Code Stop hook.

Default mode is advisory to avoid blocking ordinary sessions. It becomes strict if:
- BIO_DELIVERY_GATE_STRICT=1, or
- .bio_delivery_gate exists in the project root, or
- delivery/.ready_to_send exists.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def project_root() -> Path:
    cwd = Path(os.environ.get("PWD", ".")).resolve()
    cur = cwd
    while cur != cur.parent:
        if (cur / ".git").exists() or (cur / "plan.md").exists() or (cur / "delivery").exists():
            return cur
        cur = cur.parent
    return cwd


def main() -> int:
    # Drain stdin if Claude Code sends hook JSON; this script only needs cwd.
    try:
        if not sys.stdin.isatty():
            _ = sys.stdin.read()
    except Exception:
        pass

    root = project_root()
    delivery = root / "delivery"
    if not delivery.exists():
        return 0

    strict = os.environ.get("BIO_DELIVERY_GATE_STRICT") == "1" or (root / ".bio_delivery_gate").exists() or (delivery / ".ready_to_send").exists()
    proof_path = delivery / "proof.json"
    if not proof_path.exists():
        msg = "bio-delivery-gate: delivery/ exists but delivery/proof.json is missing. Run bio-goal or harness/delivery/proof.py before sending."
        print(msg, file=sys.stderr)
        return 2 if strict else 0

    try:
        proof = json.loads(proof_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"bio-delivery-gate: cannot parse {proof_path}: {e}", file=sys.stderr)
        return 2 if strict else 0

    status = proof.get("status")
    if status not in {"PASS", "PASS_WITH_WARN"}:
        print(f"bio-delivery-gate: proof status is {status}; not ready for final sending.", file=sys.stderr)
        return 2 if strict else 0

    bad = []
    for issue in proof.get("open_warnings", []) or []:
        text = str(issue)
        if "P0" in text or "P1" in text:
            bad.append(text)
    if bad:
        print("bio-delivery-gate: P0/P1 warnings remain in proof:", file=sys.stderr)
        for b in bad[:20]:
            print(f"- {b}", file=sys.stderr)
        return 2 if strict else 0

    print(f"bio-delivery-gate: {status}; proof ok ({proof_path})", file=sys.stderr)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
