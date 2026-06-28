#!/usr/bin/env python3
"""交付包去冗余检查：客户包里不该有多版本/草稿/重复文件。stdlib only。
- P2：版本/副本命名(_v2/_final/副本/(2)/ N./old/copy/bak/_new) —— 多半是没清干净的旧版。
- P3：内容完全相同(同 md5)的重复文件 —— 可能是多余副本。
退出码：有 P2 → 1（打包前应处理），仅 P3 → 0。"""
import os, sys, re, json, hashlib
from collections import defaultdict

EXCLUDE_DIRS = {".git", ".bio_harness", "__MACOSX", "_archive"}
EXCLUDE_NAMES = {"proof.json", "goal_proof.md", ".DS_Store", "Thumbs.db"}
VERSIONISH = re.compile(
    r"副本|备份|_v\d|_final\b|_最终|_定稿|\(\d+\)|（\d+）|"
    r"[ _\-](copy|bak|backup|old|new)\b|\.bak\b|_新|_旧| \d+\.",
    re.IGNORECASE)


def scan(root):
    findings, by_md5 = [], defaultdict(list)
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in EXCLUDE_DIRS]
        for f in fns:
            if f in EXCLUDE_NAMES or f.startswith("."):
                continue
            full = os.path.join(dp, f)
            rel = os.path.relpath(full, root)
            if VERSIONISH.search(f):
                findings.append({"severity": "P2", "code": "REDUNDANT_VERSION_NAME",
                                 "file": rel, "message": "像多版本/草稿/副本，客户包不应保留"})
            try:
                by_md5[hashlib.md5(open(full, "rb").read()).hexdigest()].append(rel)
            except Exception:
                pass
    for digest, paths in by_md5.items():
        if len(paths) > 1:
            findings.append({"severity": "P3", "code": "DUPLICATE_CONTENT",
                             "file": "; ".join(paths[:5]),
                             "message": f"{len(paths)} 个文件内容完全相同，可能多余"})
    return findings


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "delivery"
    findings = scan(os.path.abspath(target))
    print(json.dumps(findings, ensure_ascii=False, indent=2))
    p2 = [x for x in findings if x["severity"] == "P2"]
    if p2:
        print(f"dedup_check: 发现 {len(p2)} 处多版本/副本残留，打包前清理。", file=sys.stderr)
    return 1 if p2 else 0


if __name__ == "__main__":
    raise SystemExit(main())
