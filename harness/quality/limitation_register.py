#!/usr/bin/env python3
"""limitation_register.py — 抽取结果目录里所有"做不了/边界"字符串，逼出一张"理由核实"登记表。

动机（见 docs/SHARED-AUDIT.md §7）：数字复算只证"数字非造假"，证不了"方法对"。
一个 `not_run / not_assessable / missing_X` 是**待验证 claim，不是事实**——必须回到独立源头
验 blocker 真伪。曾漏判："用假理由(missing_subject_ids)跳过 mandated 混合模型"，而该数据集其实有 subject_id。

本脚本做机械兜底（不替代人判，是逼人别漏）：
  1. 扫 results/ audit/ 下 *.tsv/*.md/*.json/*.txt，抽全部 limitation 字符串 → 登记表。
  2. 邻近没有证据指针（文件路径/数值/sha/probe/引用）的 limitation → P2（"理由未附证据，去核实"）。
  3. 断言式缺失（missing_X / no_X_available / due_missing_X）→ 单列，最像 FALSE_REASON 的一类。
  4. 可选 --present-col COL --in FILE：若 FILE.COL 实为非空，而登记表里有人声称该 COL 缺失
     → P1（"声称缺失但源表有值"，即 FALSE_REASON 嫌疑），直接机械复现 Tier3 那类漏判。

仅用 Python stdlib。用法：
  python3 limitation_register.py <项目根> [--json] [--strict]
  python3 limitation_register.py <项目根> --present-col subject_id --in results/stage1/master.tsv
  python3 limitation_register.py --selftest
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import Issue, exit_code_for, print_issues, project_root, read_text  # noqa: E402

# limitation 词典（小写匹配）。分两类：一般边界 vs 断言式缺失（更像可证伪的假理由）。
GENERAL_TOKENS = [
    "not_run", "not_assessable", "not_testable", "not_completed", "not_supported",
    "not_applicable", "blocked", "skipped", "fallback", "deferred", "capped",
    "placeholder", "stub", "no_lme4", "proxy_no_", "downgrad",
]
ASSERTION_TOKENS = [  # 断言"某数据/字段/工具缺失"——最该被 reason-truthing 的一类
    "missing_subject", "missing_", "no_subject", "no_coordinate", "no_raw",
    "_absent", "due_missing", "due_to_missing", "not_available", "no_", "unavailable",
]
# 证据指针的迹象：邻近有这些 → 认为该 limitation 至少附了可核实的线索
EVIDENCE_HINTS = re.compile(
    r"(\.tsv|\.csv|\.h5|\.rds|\.md|\.json|\.tar|sha256|md5|probe|"
    r"\bp\s*=|\bfdr|n\s*=|\d{2,}|GSE\d+|GSM\d+|:\d+|doi|pmid)",
    re.IGNORECASE,
)
SCAN_DIRS = ["results", "result", "output", "outputs", "analysis", "audit"]
SCAN_EXT = {".tsv", ".csv", ".md", ".json", ".txt", ".log", ".status"}
UNKNOWNISH = {"", "unknown", "na", "n/a", "none", "null", "nan", "unassigned"}


def _iter_files(root: Path):
    for d in SCAN_DIRS:
        base = root / d
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_file() and p.suffix.lower() in SCAN_EXT and not p.name.startswith("._"):
                yield p


def scan_register(root: Path):
    """返回 [(path_str, line_no, token, is_assertion, line_text)]。"""
    hits = []
    all_tokens = [(t, False) for t in GENERAL_TOKENS] + [(t, True) for t in ASSERTION_TOKENS]
    for p in _iter_files(root):
        try:
            text = read_text(p)
        except Exception:
            continue
        rel = str(p.relative_to(root))
        for ln, line in enumerate(text.splitlines(), 1):
            low = line.lower()
            for token, is_assert in all_tokens:
                if token in low:
                    hits.append((rel, ln, token, is_assert, line.strip()[:240]))
                    break  # 一行只记一次，避免同行多 token 刷屏
    return hits


def _load_column(path: Path, col: str):
    """读某列非空值数，用 csv.reader（带引号/内嵌 JSON 列用 csv 比裸 split 稳妥）。"""
    import csv as _csv
    try:
        with open(path, encoding="utf-8", newline="") as f:
            first = f.readline()
            delim = "\t" if "\t" in first else ","
            f.seek(0)
            rows = list(_csv.reader(f, delimiter=delim))
    except Exception:
        return None, 0
    if not rows or col not in rows[0]:
        return None, 0
    idx = rows[0].index(col)
    nonempty = sum(1 for r in rows[1:] if idx < len(r) and r[idx].strip().lower() not in UNKNOWNISH)
    return nonempty, len(rows) - 1


def build_issues(root: Path, present_col: str = "", present_in: str = "") -> list:
    issues = []
    hits = scan_register(root)
    if not hits:
        return issues

    n_total = len(hits)
    n_assert = sum(1 for h in hits if h[3])
    n_no_evidence = 0
    for rel, ln, token, is_assert, line_text in hits:
        has_ev = bool(EVIDENCE_HINTS.search(line_text))
        if not has_ev:
            n_no_evidence += 1
            issues.append(Issue(
                severity="P2",
                code="LIMITATION_NO_EVIDENCE",
                message=f'"{token}" 无邻近证据指针，需回独立源头核实 blocker 真伪',
                path=f"{rel}:{ln}",
                hint="reason-truthing：这是待验证 claim 不是事实；附 文件:行/数值/sha 证据或改判",
            ))

    # 断言式缺失单独汇总（最该被人核实的一类）
    if n_assert:
        issues.append(Issue(
            severity="P2",
            code="LIMITATION_ASSERTION_ABSENCE",
            message=f"{n_assert} 处断言式'缺失/做不了'(missing_X/no_X/due_missing)，逐个验 blocker 是否真成立",
            path=str(root / "results"),
            hint="曾漏判：假理由 missing_subject_ids 跳过 mandated 模型，而该集实有该列",
        ))

    # 可选：机械反证——"声称某列缺失"但源表里该列其实有值。工具只**提名 SUSPECT**，人来判死
    # （机械匹配必有假阳；且反证的源表读取本身必须 quoting-aware，见 _load_column）。
    if present_col and present_in:
        src = (root / present_in) if not os.path.isabs(present_in) else Path(present_in)
        nonempty, total = _load_column(src, present_col)
        root_word = re.escape(present_col.lower().replace("_id", ""))
        absent_re = re.compile(r"(missing|no[_ ]|without|lack|absent|unavailable|due[_ ]?missing)[a-z0-9_ ]{0,20}" + root_word)
        claims = [h for h in hits
                  if absent_re.search(h[4].lower())
                  and "forbidden" not in h[0].lower()]   # 规则文档在说"别做X"，不是声称缺失
        if nonempty and claims:
            for rel, ln, token, _a, _t in claims[:20]:
                issues.append(Issue(
                    severity="P2",
                    code="FALSE_REASON_SUSPECT",
                    message=f'该行声称 "{present_col}" 缺失，但 {present_in} 该列有 {nonempty}/{total} 非空值 → 疑似 FALSE_REASON',
                    path=f"{rel}:{ln}",
                    hint="机械提名非判死：核对该 limitation 针对的数据集是否真缺该列；不实则改标注并补跑",
                ))

    # 登记表总览（INFO，恒不 fail，保证登记表可见）
    issues.append(Issue(
        severity="INFO",
        code="LIMITATION_REGISTER",
        message=f"共 {n_total} 处 limitation（断言式 {n_assert}，无证据 {n_no_evidence}）——逐条 reason-truthing",
        path=str(root),
        hint="--json 看全表；docs/SHARED-AUDIT.md §7",
    ))
    return issues


def _selftest() -> int:
    import tempfile
    ok = True
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "results" / "stage4").mkdir(parents=True)
        (root / "results" / "stage1").mkdir(parents=True)
        # 复现 Tier3：假理由 missing subject ids
        (root / "results" / "stage4" / "coupling.tsv").write_text(
            "dataset_id\tmodel\nSCP259\tspearman_proxy_no_lme4_due_missing_subject_ids_in_public_scRNA\n",
            encoding="utf-8")
        # 源表其实有 subject_id
        (root / "results" / "stage1" / "master.tsv").write_text(
            "dataset_id\tsubject_id\nSCP259\tN10\nSCP259\tN11\n", encoding="utf-8")
        # 一条附了证据的 limitation（不该报 no-evidence）
        (root / "results" / "stage7" ).mkdir(parents=True)
        (root / "results" / "stage7" / "gf.tsv").write_text(
            "status\tboundary\nnot_run\tGeneformer needs GPU; sha256=abc123 probe at 2026\n", encoding="utf-8")

        issues = build_issues(root, present_col="subject_id", present_in="results/stage1/master.tsv")
        codes = [i.code for i in issues]
        assert "FALSE_REASON_SUSPECT" in codes, "应机械提名假理由 SUSPECT"
        assert any(i.code == "FALSE_REASON_SUSPECT" and i.severity == "P2" for i in issues), "SUSPECT 应 P2（提名非判死）"
        assert "LIMITATION_REGISTER" in codes, "应有登记表总览"
        # gf.tsv 那条 not_run 附了 sha256/probe → 不应进 no-evidence
        no_ev_paths = [i.path for i in issues if i.code == "LIMITATION_NO_EVIDENCE"]
        assert not any("gf.tsv" in p for p in no_ev_paths), "附证据的 limitation 不该报无证据"
        print("selftest PASS:", codes)
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="抽取 limitation 字符串并逼出理由核实登记表")
    ap.add_argument("project", nargs="?", default=".")
    ap.add_argument("--present-col", default="", help="机械反证：声称缺失的列名")
    ap.add_argument("--in", dest="present_in", default="", help="含该列的源表（项目相对或绝对路径）")
    ap.add_argument("--strict", action="store_true", help="P2 也计入失败退出码")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return _selftest()
    root = project_root(args.project)
    issues = build_issues(root, args.present_col, args.present_in)
    print_issues(issues, args.json)
    return exit_code_for(issues, args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
