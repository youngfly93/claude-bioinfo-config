#!/usr/bin/env python3
"""numeric_reference_verify.py — 读 numeric_reference.tsv，从源表**真重算**每个承重数字并逐位 diff。

补 `numeric_claims_check.py` 的缺口：那个只检查 source_file/column **填没填**，不真算。
本脚本让任何会话（有没有记忆都行）对**同一冻结快照**跑同一套 recompute，得同一份结论——
把"两个 LLM 主观读同一堆文件"变成"同一脚本对同一快照"，divergence 从掷骰子变成可定位事件。

**quoting-aware（csv.reader）**：带引号/内嵌 JSON 的 TSV 裸 split/awk 会错位（本项目真踩过）。

### numeric_reference.tsv 列（# 开头为注释行，跳过）
    key  expected  source_file  recompute  tolerance  note
- source_file：相对项目根的表路径。
- recompute（小 DSL，从 source_file 算出一个数）：
    rows                         数据行数
    count:COL OP VAL             满足条件的行数（OP ∈ < > <= >= == !=；VAL 数值或字符串）
    cell:FCOL=FVAL[&FCOL2=FVAL2];COL   过滤后首行 COL 的值
    nunique:COL[|FCOL=FVAL]      COL 去重非空计数（可过滤）
    agg:FUNC:COL[|FCOL=FVAL]     FUNC ∈ sum/mean/max/min
    script:CMD                   复杂重算（HK metafor / CV 泄漏…）→ 不自动判、记 INFO 指向项目脚本
    manual:DESC                  人工核 → INFO
- tolerance：绝对值（默认 0=整数精确）；或 `rel:0.05`（相对 5%）。
- 不一致 → P1；script/manual → INFO。

用法：
    python3 numeric_reference_verify.py <项目根> [--ref numeric_reference.tsv] [--json] [--strict]
    python3 numeric_reference_verify.py --selftest
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import Issue, exit_code_for, print_issues, project_root  # noqa: E402

OPS = {"<": lambda a, b: a < b, ">": lambda a, b: a > b, "<=": lambda a, b: a <= b,
       ">=": lambda a, b: a >= b, "==": lambda a, b: a == b, "!=": lambda a, b: a != b}
UNKNOWNISH = {"", "unknown", "na", "n/a", "none", "null", "nan"}


def _read(path):
    with open(path, encoding="utf-8", newline="") as f:
        first = f.readline()
        delim = "\t" if "\t" in first else ","
        f.seek(0)
        allrows = list(csv.reader(f, delimiter=delim))
    if not allrows:
        return [], []
    header = allrows[0]  # 第一行永远当表头（numeric_reference 表头是 "# key..."）
    data = [r for r in allrows[1:] if r and not r[0].startswith("#")]  # 之后的 # 行=注释
    return header, data


def _num(s):
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _match(parts, header, expr):
    # expr = "COL OP VAL"；返回 bool
    for op in ("<=", ">=", "!=", "==", "<", ">"):
        if op in expr:
            col, val = expr.split(op, 1)
            col, val = col.strip(), val.strip()
            if col not in header:
                return None
            cell = parts[header.index(col)].strip() if header.index(col) < len(parts) else ""
            cn, vn = _num(cell), _num(val)
            if cn is not None and vn is not None:
                return OPS[op](cn, vn)
            return OPS[op](cell, val)  # 字符串比较（== / !=）
    return None


def _filter(rows, header, sel):
    # sel = "FCOL=FVAL&FCOL2=FVAL2"
    out = rows
    if sel:
        for cond in sel.split("&"):
            fc, fv = cond.split("=", 1)
            fc, fv = fc.strip(), fv.strip()
            if fc not in header:
                return []
            i = header.index(fc)
            out = [r for r in out if i < len(r) and r[i].strip() == fv]
    return out


def recompute(root: Path, source_file: str, spec: str):
    """返回 (value_or_None, note)。None 表示无法自动算（script/manual/错误）。"""
    if spec.startswith(("script:", "manual:")):
        return None, spec
    p = root / source_file
    if not p.exists():
        return None, f"source_file 不存在: {source_file}"
    header, rows = _read(p)
    if not header:
        return None, "空表"
    try:
        if spec == "rows":
            return float(len(rows)), ""
        if spec.startswith("count:"):
            expr = spec[6:]
            return float(sum(1 for r in rows if _match(r, header, expr))), ""
        if spec.startswith("cell:"):
            body = spec[5:]
            sel, col = (body.rsplit(";", 1) + [""])[:2] if ";" in body else ("", body)
            f = _filter(rows, header, sel)
            if col not in header or not f:
                return None, f"cell 未命中 (col={col}, sel={sel})"
            v = f[0][header.index(col)].strip()
            return (_num(v) if _num(v) is not None else v), ""
        if spec.startswith("nunique:"):
            body = spec[8:]
            col, sel = (body.split("|", 1) + [""])[:2]
            f = _filter(rows, header, sel)
            if col not in header:
                return None, f"nunique 无列 {col}"
            i = header.index(col)
            return float(len({r[i].strip() for r in f if i < len(r) and r[i].strip().lower() not in UNKNOWNISH})), ""
        if spec.startswith("agg:"):
            _, func, rest = spec.split(":", 2)
            col, sel = (rest.split("|", 1) + [""])[:2]
            f = _filter(rows, header, sel)
            if col not in header:
                return None, f"agg 无列 {col}"
            i = header.index(col)
            vals = [_num(r[i]) for r in f if i < len(r) and _num(r[i]) is not None]
            if not vals:
                return None, "agg 无数值"
            funcs = {"sum": sum, "mean": lambda x: sum(x) / len(x), "max": max, "min": min,
                     "median": lambda x: (sorted(x)[(len(x) - 1) // 2] + sorted(x)[len(x) // 2]) / 2}
            return funcs[func](vals), ""
        return None, f"未知 recompute: {spec}"
    except Exception as e:  # noqa: BLE001
        return None, f"recompute 异常: {e}"


def _close(expected: str, got, tol: str) -> bool:
    en, gn = _num(expected), (got if isinstance(got, float) else _num(got))
    if en is None or gn is None:  # 字符串精确
        return str(expected).strip() == str(got).strip()
    if tol and tol.startswith("rel:"):
        r = float(tol[4:])
        return abs(gn - en) <= abs(en) * r + 1e-12
    t = _num(tol) or 0.0
    return abs(gn - en) <= t + 1e-9


def build_issues(root: Path, ref: str) -> list:
    issues = []
    refp = root / ref
    if not refp.exists():
        return [Issue("P2", "NUMREF_MISSING", f"缺 {ref}", str(root),
                      hint="建一份 numeric_reference.tsv（key/expected/source_file/recompute/tolerance）")]
    header, rows = _read(refp)
    need = {"key", "expected", "source_file", "recompute"}
    if not need.issubset(set(h.strip().lstrip("#").strip() for h in header)):
        return [Issue("P1", "NUMREF_SCHEMA", f"{ref} 需列 {need}，实际 {header}", str(refp))]
    idx = {h.strip().lstrip("#").strip(): i for i, h in enumerate(header)}
    n_ok = n_manual = 0
    for r in rows:
        def g(c): return r[idx[c]].strip() if c in idx and idx[c] < len(r) else ""
        key, exp, sf, spec, tol = g("key"), g("expected"), g("source_file"), g("recompute"), g("tolerance")
        got, note = recompute(root, sf, spec)
        if got is None:
            if spec.startswith(("script:", "manual:")):
                n_manual += 1
                issues.append(Issue("INFO", "NUMREF_MANUAL", f"{key}: {spec}（非自动，人工/脚本核）", sf))
            else:
                issues.append(Issue("P1", "NUMREF_RECOMPUTE_FAIL", f"{key}: 无法重算 — {note}", sf,
                                    hint="检查 source_file/recompute DSL 或该文件是否被改"))
            continue
        if _close(exp, got, tol):
            n_ok += 1
        else:
            issues.append(Issue("P1", "NUMREF_MISMATCH",
                                f"{key}: 期望 {exp} 但源表重算 {got}（tol={tol or '0'}）", sf,
                                hint="要么数字写错，要么源表变了（先排除文件被改/被修）"))
    issues.append(Issue("INFO", "NUMREF_SUMMARY",
                        f"{len(rows)} 条：{n_ok} 逐位一致 / {n_manual} 人工-脚本 / {len(rows)-n_ok-n_manual} 待查", str(refp)))
    return issues


def _selftest() -> int:
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "results").mkdir()
        (root / "results" / "meta.tsv").write_text(
            "contrast\tmetric\thk_effect\tfdr\n"
            "IBD_vs_HC\tWTAP_METTL14\t0.6660\t0.004\n"
            "IBD_vs_HC\tsynergy\t0.015\t0.937\n"
            "CD_vs_HC\tWTAP_METTL14\t0.497\t0.02\n", encoding="utf-8")
        (root / "results" / "cells.tsv").write_text(
            "gene\tsubject\tfdr\nA\tS1\t0.01\nB\tS1\t0.2\nC\tS2\t0.001\nD\tS3\t0.9\n", encoding="utf-8")
        ref = ("# key\texpected\tsource_file\trecompute\ttolerance\tnote\n"
               "hk_wtap\t0.6660\tresults/meta.tsv\tcell:contrast=IBD_vs_HC&metric=WTAP_METTL14;hk_effect\t0.001\t-\n"
               "synergy_p\t0.937\tresults/meta.tsv\tcell:metric=synergy;fdr\t0.001\tnull\n"
               "n_rows\t3\tresults/meta.tsv\trows\t0\t-\n"
               "sig_cells\t2\tresults/cells.tsv\tcount:fdr<0.05\t0\t-\n"
               "n_subject\t3\tresults/cells.tsv\tnunique:subject\t0\t-\n"
               "hk_max\t0.6660\tresults/meta.tsv\tagg:max:hk_effect\t0.001\t-\n"
               "cv_leak\t0\tresults/cells.tsv\tscript:verify_cv.py\t0\t复杂\n"
               "WRONG\t99\tresults/meta.tsv\trows\t0\t故意错\n")
        (root / "numeric_reference.tsv").write_text(ref, encoding="utf-8")
        issues = build_issues(root, "numeric_reference.tsv")
        codes = [i.code for i in issues]
        mism = [i for i in issues if i.code == "NUMREF_MISMATCH"]
        assert len(mism) == 1 and "WRONG" in mism[0].message, "应恰好抓到 1 个故意错"
        assert any(i.code == "NUMREF_MANUAL" for i in issues), "script: 应记 MANUAL"
        assert not any(i.code == "NUMREF_RECOMPUTE_FAIL" for i in issues), "不该有重算失败"
        summ = [i for i in issues if i.code == "NUMREF_SUMMARY"][0]
        assert "6 逐位一致" in summ.message, summ.message
        print("selftest PASS:", summ.message)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="从源表重算并逐位 diff numeric_reference.tsv")
    ap.add_argument("project", nargs="?", default=".")
    ap.add_argument("--ref", default="numeric_reference.tsv")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return _selftest()
    issues = build_issues(project_root(args.project), args.ref)
    print_issues(issues, args.json)
    return exit_code_for(issues, args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
