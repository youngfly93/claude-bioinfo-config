#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Import common helpers without requiring installation.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "quality"))
from common import find_plan, git_commit, md5_file, sha256_file

SCHEMA = "bio-harness-proof.v1"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _harness_version() -> str:
    """记真正用的是哪版 harness——每条交付/反馈能对到具体 commit（配 bio-feedback 复盘）。
    装成插件(非 git 仓)时回退静态串。"""
    try:
        c = git_commit(Path(__file__).resolve().parents[2])  # harness 仓根
        if c:
            return f"bio-harness@{c[:10]}"
    except Exception:
        pass
    return "bio-harness.v1"


def proof_paths(root: Path) -> tuple[Path, Path]:
    d = root / "delivery"
    d.mkdir(exist_ok=True)
    return d / "proof.json", d / "goal_proof.md"


def load(root: Path) -> dict:
    p, _ = proof_paths(root)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    plan = find_plan(root)
    return {
        "schema_version": SCHEMA,
        "created_at": now(),
        "updated_at": now(),
        "project_root": str(root),
        "git_commit": git_commit(root),
        "plan_path": str(plan.relative_to(root)) if plan else None,
        "plan_sha256": sha256_file(plan) if plan and plan.exists() else None,
        "harness_version": _harness_version(),
        "status": "IN_PROGRESS",
        "commands": [],
        "artifacts": [],
        "open_warnings": [],
        "manual_warnings": [],
    }


_TABLE_ROW = re.compile(r"^\|\s*(P[0-3]|INFO)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*$")


def _parse_findings(stdout: str) -> list:
    """从命令 stdout 提取 findings。支持两种 harness 输出格式：
    1) JSON 数组（delivery 类检查 structure_check/dedup_check/privacy_scan）；
    2) `| severity | code | path | message |` 表格（quality 类 common.print_issues）。"""
    out = []
    s = (stdout or "").strip()
    if s.startswith("["):
        try:
            data = json.loads(s)
        except (ValueError, TypeError):
            data = None
        if isinstance(data, list):
            for d in data:
                if isinstance(d, dict) and d.get("severity"):
                    out.append({
                        "severity": str(d.get("severity")),
                        "code": str(d.get("code", "")),
                        "path": str(d.get("path") or d.get("file", "")),
                        "message": str(d.get("message", "")),
                    })
            return out
    for line in (stdout or "").splitlines():
        m = _TABLE_ROW.match(line)
        if m:
            out.append({"severity": m.group(1), "code": m.group(2), "path": m.group(3), "message": m.group(4)})
    return out


def _refresh_open_warnings(proof: dict) -> None:
    """open_warnings = 各命令最新记录里的 P2/P3 findings（自动收集）+ manual_warnings（finalize --warning）。
    幂等：每次 save 从命令记录重算，避免重跑命令时重复/陈旧。P0/P1 会让命令 exit≠0 → 已被裁判，不进 warnings。"""
    latest = {}
    for c in proof.get("commands", []) or []:
        latest[c.get("name")] = c
    derived = []
    for name, c in latest.items():
        for f in c.get("findings", []) or []:
            if f.get("severity") in ("P2", "P3"):
                entry = f"{name}: {f.get('severity')} {f.get('code', '')} {f.get('path', '')} — {f.get('message', '')}".strip()
                if entry not in derived:
                    derived.append(entry)
    proof["open_warnings"] = derived + [w for w in (proof.get("manual_warnings", []) or []) if w not in derived]


def save(root: Path, proof: dict) -> None:
    _refresh_open_warnings(proof)
    proof["updated_at"] = now()
    json_path, md_path = proof_paths(root)
    json_path.write_text(json.dumps(proof, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(proof), encoding="utf-8")


def render_markdown(proof: dict) -> str:
    lines = []
    lines.append("# Goal proof")
    lines.append("")
    lines.append(f"- status: `{proof.get('status')}`")
    lines.append(f"- git_commit: `{proof.get('git_commit')}`")
    lines.append(f"- plan_path: `{proof.get('plan_path')}`")
    lines.append(f"- plan_sha256: `{proof.get('plan_sha256')}`")
    lines.append(f"- harness_version: `{proof.get('harness_version')}`")
    lines.append("")
    lines.append("## Commands")
    lines.append("")
    if proof.get("commands"):
        lines.append("| name | exit | command | stdout | stderr |")
        lines.append("|---|---:|---|---|---|")
        for c in proof["commands"]:
            cmd = c.get("cmd", "").replace("|", "\\|")
            lines.append(f"| {c.get('name')} | {c.get('exit_code')} | `{cmd}` | {c.get('stdout_log','')} | {c.get('stderr_log','')} |")
    else:
        lines.append("No commands recorded yet.")
    lines.append("")
    lines.append("## Artifacts")
    lines.append("")
    if proof.get("artifacts"):
        lines.append("| path | size | md5 |")
        lines.append("|---|---:|---|")
        for a in proof["artifacts"]:
            lines.append(f"| {a.get('path')} | {a.get('size_bytes')} | `{a.get('md5')}` |")
    else:
        lines.append("No artifacts recorded yet.")
    lines.append("")
    lines.append("## Open warnings")
    lines.append("")
    if proof.get("open_warnings"):
        for w in proof["open_warnings"]:
            lines.append(f"- {w}")
    else:
        lines.append("None.")
    lines.append("")
    return "\n".join(lines)


def cmd_init(root: Path) -> int:
    proof = load(root)
    save(root, proof)
    print(json.dumps({"proof_json": str(proof_paths(root)[0]), "goal_proof_md": str(proof_paths(root)[1])}, ensure_ascii=False, indent=2))
    return 0


def cmd_run(root: Path, name: str, command: list[str]) -> int:
    proof = load(root)
    logs = root / ".bio_harness" / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in name)
    stdout_log = logs / f"{stamp}_{safe_name}.stdout.txt"
    stderr_log = logs / f"{stamp}_{safe_name}.stderr.txt"
    started = now()
    cp = subprocess.run(command, cwd=str(root), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    stdout_log.write_text(cp.stdout, encoding="utf-8", errors="replace")
    stderr_log.write_text(cp.stderr, encoding="utf-8", errors="replace")
    record = {
        "name": name,
        "cmd": " ".join(shlex.quote(c) for c in command),
        "started_at": started,
        "finished_at": now(),
        "exit_code": cp.returncode,
        "stdout_log": str(stdout_log.relative_to(root)),
        "stderr_log": str(stderr_log.relative_to(root)),
        "findings": _parse_findings(cp.stdout),
    }
    proof.setdefault("commands", []).append(record)
    if cp.returncode != 0:
        proof["status"] = "FAIL"
    save(root, proof)
    if cp.stdout:
        print(cp.stdout, end="")
    if cp.stderr:
        print(cp.stderr, end="", file=sys.stderr)
    return cp.returncode


def cmd_artifact(root: Path, paths: list[str]) -> int:
    proof = load(root)
    for item in paths:
        path = (root / item).resolve() if not Path(item).is_absolute() else Path(item)
        if not path.exists() or not path.is_file():
            print(f"artifact not found or not file: {path}", file=sys.stderr)
            return 1
        try:
            rel = str(path.relative_to(root))
        except ValueError:
            rel = str(path)
        proof.setdefault("artifacts", []).append({"path": rel, "size_bytes": path.stat().st_size, "md5": md5_file(path), "sha256": sha256_file(path)})
    save(root, proof)
    return 0


REQUIRED_COMMANDS = ["preflight", "validate_strict", "audit", "ai_scan", "privacy_scan", "structure_check", "package"]


def _pass_blockers(root: Path, proof: dict) -> list[str]:
    """PASS / PASS_WITH_WARN 前必须满足的硬条件；返回未满足项（空=可放行）。"""
    blockers = []
    cmds = {c.get("name"): c for c in (proof.get("commands") or [])}
    for name in REQUIRED_COMMANDS:
        if name not in cmds:
            blockers.append(f"缺命令记录: {name}")
        elif cmds[name].get("exit_code") not in (0, None):
            blockers.append(f"命令未通过(exit≠0): {name}")
    paths = [str(a.get("path", "")) for a in (proof.get("artifacts") or [])]
    if not any(p.endswith(".zip") for p in paths):
        blockers.append("缺 zip 产物(proof.artifacts 无 .zip；先跑 package + collect)")
    if not (root / "audit" / "audit.json").exists():
        blockers.append("缺 audit/audit.json")
    return blockers


def cmd_collect(root: Path) -> int:
    """自动把交付区的 zip(及同名 .md5 若有)登记进 proof.artifacts，免得 artifact 表为空。"""
    proof = load(root)
    existing = {a.get("path") for a in (proof.get("artifacts") or [])}
    n = 0
    cands = sorted(root.glob("*.zip")) + sorted((root / "delivery").glob("*.zip"))
    for z in cands:
        for f in (z, z.with_suffix(z.suffix + ".md5")):
            if not (f.exists() and f.is_file()):
                continue
            rel = str(f.relative_to(root)) if f.is_relative_to(root) else str(f)
            if rel in existing:
                continue
            proof.setdefault("artifacts", []).append(
                {"path": rel, "size_bytes": f.stat().st_size, "md5": md5_file(f), "sha256": sha256_file(f)})
            existing.add(rel); n += 1
    save(root, proof)
    print(f"collected {n} artifact(s)")
    return 0


def cmd_finalize(root: Path, status: str, warnings: list[str]) -> int:
    proof = load(root)
    proof.setdefault("manual_warnings", []).extend(warnings)
    if status in {"PASS", "PASS_WITH_WARN"}:
        blockers = _pass_blockers(root, proof)
        if blockers:
            proof["status"] = "FAIL"
            save(root, proof)
            print("proof.py finalize 拒绝 PASS —— 以下硬条件未满足：", file=sys.stderr)
            for b in blockers:
                print(f"- {b}", file=sys.stderr)
            return 1
    proof["status"] = status
    save(root, proof)
    print(render_markdown(proof))
    return 0 if status in {"PASS", "PASS_WITH_WARN"} else 1


def cmd_status(root: Path, require_pass: bool = False) -> int:
    proof = load(root)
    save(root, proof)
    print(render_markdown(proof))
    ok = {"PASS", "PASS_WITH_WARN"} if require_pass else {"PASS", "PASS_WITH_WARN", "IN_PROGRESS"}
    return 0 if proof.get("status") in ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Create and update delivery/proof.json + goal_proof.md")
    sub = ap.add_subparsers(dest="cmd", required=True)
    init = sub.add_parser("init")
    init.add_argument("project", nargs="?", default=".")
    run = sub.add_parser("run")
    run.add_argument("--name", required=True)
    run.add_argument("project")
    run.add_argument("command", nargs=argparse.REMAINDER)
    art = sub.add_parser("artifact")
    art.add_argument("project")
    art.add_argument("paths", nargs="+")
    col = sub.add_parser("collect")
    col.add_argument("project", nargs="?", default=".")
    fin = sub.add_parser("finalize")
    fin.add_argument("project")
    fin.add_argument("--status", choices=["PASS", "PASS_WITH_WARN", "FAIL"], required=True)
    fin.add_argument("--warning", action="append", default=[])
    st = sub.add_parser("status")
    st.add_argument("project", nargs="?", default=".")
    st.add_argument("--require-pass", action="store_true")
    args = ap.parse_args()

    if args.cmd == "init":
        return cmd_init(Path(args.project).resolve())
    if args.cmd == "run":
        if args.command and args.command[0] == "--":
            args.command = args.command[1:]
        if not args.command:
            print("proof.py run requires a command after --", file=sys.stderr)
            return 2
        return cmd_run(Path(args.project).resolve(), args.name, args.command)
    if args.cmd == "artifact":
        return cmd_artifact(Path(args.project).resolve(), args.paths)
    if args.cmd == "collect":
        return cmd_collect(Path(args.project).resolve())
    if args.cmd == "finalize":
        return cmd_finalize(Path(args.project).resolve(), args.status, args.warning)
    if args.cmd == "status":
        return cmd_status(Path(args.project).resolve(), args.require_pass)
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
