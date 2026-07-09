#!/usr/bin/env python3
"""Advisory/strict delivery gate for Claude Code Stop hook.

Default mode is advisory to avoid blocking ordinary sessions. It becomes strict if:
- BIO_DELIVERY_GATE_STRICT=1, or
- .bio_clinical_mode exists in the project root (临床/敏感项目硬卡), or
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
    # Non-blocking: a Stop hook must return promptly. A bare/piped invocation whose
    # writer never sends EOF would make an unconditional sys.stdin.read() hang forever
    # (and stall the loop). select+os.read drains what's buffered and never blocks.
    try:
        if not sys.stdin.isatty():
            import select
            fd = sys.stdin.fileno()
            while select.select([fd], [], [], 0.0)[0]:
                if not os.read(fd, 65536):
                    break  # EOF
    except Exception:
        pass

    root = project_root()
    delivery = root / "delivery"
    if not delivery.exists():
        return 0

    # 临床/敏感项目：项目根放 .bio_clinical_mode 即强制 strict（交付门变硬卡）
    strict = (os.environ.get("BIO_DELIVERY_GATE_STRICT") == "1"
              or (root / ".bio_delivery_gate").exists()
              or (root / ".bio_clinical_mode").exists()
              or (delivery / ".ready_to_send").exists())
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

    # 不只信 status：核对每条命令的退出码，挡住"手动 finalize PASS 但某步其实 exit≠0"
    failed = [str(c.get("name")) for c in (proof.get("commands") or []) if c.get("exit_code") not in (0, None)]
    if failed:
        print(f"bio-delivery-gate: proof 记录有命令未通过(exit≠0): {', '.join(failed)}；修复后重跑再发。", file=sys.stderr)
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
