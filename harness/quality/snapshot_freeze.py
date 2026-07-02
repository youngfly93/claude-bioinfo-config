#!/usr/bin/env python3
"""snapshot_freeze.py — 给"审计目标"生成 sha256 内容清单 + 一个 snapshot_id。

为什么不用 git：数据项目常有 GB 级 venv/raw/中间件，git-init 整树又重又错。本脚本只对
**审计相关的小文件集**（results/*.tsv、audit/*.md、scripts、plan、numeric_reference…）
逐文件 sha256，出 `audit/audited_snapshot.sha256` + 顶行 `snapshot_id`（= 清单本身的 sha256）。

作用 = 冻结审计版本：任何会话对同一 snapshot_id 审 = 审的是**同一堆字节**；文件被改 → 其 hash 变 →
snapshot_id 变 → 立刻知道"不是一个事儿"（配 numeric_reference_verify / SHARED-AUDIT 用）。

用法：
    python3 snapshot_freeze.py <项目根> [--out audit/audited_snapshot.sha256]
    python3 snapshot_freeze.py <项目根> --check   # 对比现清单，报出被改/新增/删除
    python3 snapshot_freeze.py --selftest
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import Issue, exit_code_for, print_issues, project_root  # noqa: E402

# 审计相关（小、决定结论）纳入：按 top-dir + 扩展名（fnmatch 不支持 **，用显式规则更稳）
INCLUDE_BY_TOP = {"results": {".tsv", ".md", ".json"},
                  "audit": {".md", ".tsv"},
                  "scripts": {".py", ".r"}}
ROOT_FILES = {"numeric_reference.tsv", "report_claims.tsv"}
# 元文件（记录快照 id 本身）——排除，避免自引用（改协议文档不该改内容 id）
EXCLUDE_BASENAME = {"REPRO.md", "audited_snapshot.sha256"}
# 大/运行态/易变——排除
EXCLUDE_DIR = {"data", "work", "logs", "figures", "__pycache__", ".git"}
EXCLUDE_GLOB = ["*.tar", "*.tar.gz", "*.zip", "*.h5", "*.h5ad", "*.rds", "*.mtx",
                "._*", "*.dylib", "*.so", "*.png", "*.pdf"]
EXCLUDE_PATH_SUB = [".venv", "site-packages"]


def _included(rel: str) -> bool:
    parts = rel.split(os.sep)
    if any(p in EXCLUDE_DIR for p in parts):
        return False
    if any(sub in ("/" + rel) for sub in EXCLUDE_PATH_SUB):
        return False
    base = os.path.basename(rel)
    if base in EXCLUDE_BASENAME:
        return False
    if any(fnmatch.fnmatch(base, g) for g in EXCLUDE_GLOB):
        return False
    ext = os.path.splitext(base)[1].lower()
    segs = set(parts)
    # results/audit 段（在任意层级，兼容 METTL3_14_analysis/results/…）
    if segs & {"results", "audit"} and ext in {".tsv", ".md", ".json"}:
        return True
    if "scripts" in segs and ext in {".py", ".r"}:
        return True
    if len(parts) == 1 and (base in ROOT_FILES or ext == ".md"):  # 根目录真源 md/表
        return True
    return False


def collect(root: Path) -> dict:
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIR and not d.startswith(".venv")]
        for fn in filenames:
            full = Path(dirpath) / fn
            rel = str(full.relative_to(root))
            if _included(rel):
                try:
                    out[rel] = hashlib.sha256(full.read_bytes()).hexdigest()
                except OSError:
                    pass
    return out


def snapshot_id(manifest: dict) -> str:
    blob = "\n".join(f"{k}\t{v}" for k, v in sorted(manifest.items()))
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def write_manifest(root: Path, out: str) -> tuple:
    m = collect(root)
    sid = snapshot_id(m)
    p = root / out
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# snapshot_id: {sid}", f"# n_files: {len(m)}",
             "# 冻结审计版本（sha256 内容清单）。审计文件头写 audited_snapshot=<snapshot_id>。"]
    lines += [f"{h}  {k}" for k, h in sorted(m.items())]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return sid, len(m), p


def check(root: Path, out: str) -> list:
    p = root / out
    if not p.exists():
        return [Issue("P2", "SNAPSHOT_MISSING", f"缺 {out}，先跑一次生成", str(root))]
    prev = {}
    for ln in p.read_text(encoding="utf-8").splitlines():
        if ln.startswith("#") or not ln.strip():
            continue
        h, _, rel = ln.partition("  ")
        prev[rel] = h
    cur = collect(root)
    issues = []
    for rel in sorted(set(prev) | set(cur)):
        if rel not in cur:
            issues.append(Issue("P1", "SNAPSHOT_DELETED", f"清单里有、现已删除: {rel}", rel))
        elif rel not in prev:
            issues.append(Issue("P2", "SNAPSHOT_ADDED", f"新增（不在冻结清单）: {rel}", rel))
        elif prev[rel] != cur[rel]:
            issues.append(Issue("P1", "SNAPSHOT_CHANGED", f"内容变了（hash 不同）: {rel}", rel,
                                hint="审移动靶的信号：这文件在冻结后被改/被修，先分清再归因"))
    issues.append(Issue("INFO", "SNAPSHOT_ID",
                        f"当前 snapshot_id={snapshot_id(cur)}（清单记={prev and snapshot_id({k:prev[k] for k in prev})})", str(p)))
    return issues


def _selftest() -> int:
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "results").mkdir()
        (root / "results" / "a.tsv").write_text("x\t1\n", encoding="utf-8")
        (root / "data").mkdir()
        (root / "data" / "big.tar").write_text("HUGE", encoding="utf-8")  # 应排除
        sid1, n1, _ = write_manifest(root, "audit/snap.sha256")
        assert n1 == 1, f"只该纳入 1 个(a.tsv)，实际 {n1}"
        # 改文件 → check 应报 CHANGED
        (root / "results" / "a.tsv").write_text("x\t2\n", encoding="utf-8")
        iss = check(root, "audit/snap.sha256")
        assert any(i.code == "SNAPSHOT_CHANGED" for i in iss), "改文件应报 CHANGED"
        sid2 = snapshot_id(collect(root))
        assert sid1 != sid2, "改后 snapshot_id 应变"
        print(f"selftest PASS: sid1={sid1} sid2={sid2} 排除 data/big.tar ✓")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="生成/校验审计版本 sha256 冻结清单")
    ap.add_argument("project", nargs="?", default=".")
    ap.add_argument("--out", default="audit/audited_snapshot.sha256")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return _selftest()
    root = project_root(args.project)
    if args.check:
        issues = check(root, args.out)
        print_issues(issues, args.json)
        return exit_code_for(issues, args.strict)
    sid, n, p = write_manifest(root, args.out)
    print(f"snapshot_id={sid}  n_files={n}  →  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
