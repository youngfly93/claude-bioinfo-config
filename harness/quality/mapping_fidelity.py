#!/usr/bin/env python3
"""mapping_fidelity.py — 查受控词表列的 raw→mapped 保真度，抓"静默折进 unknown"与"整类被丢"。

动机（见 docs/SHARED-AUDIT.md §7）：门控/映射要回溯 RAW 源字段，不能拿同源派生量自证。
曾漏判：主队列 432 个 LeftColon/RightColon 样本，raw 字段明明有值，却被静默折进 `site=unknown`、
`site_coverage` 隐去、未披露——违反肠段分层且污染下游交互 contrast。数字复算发现不了这类，因为
它不是数字错，是"raw 有值但 mapped 丢了"。

本脚本对一张表：给 mapped 列 + raw 来源（另一列，或某列内嵌 JSON 的 key），逐行判：
  raw 有值 且 mapped=unknown/空  → 折进(collapse)。
  某 raw 类别在 mapped 列从不出现 → 整类被静默丢(dropped vocab)。
按 --group-by（如 dataset_id）分组报折进率；超阈值或有整类被丢 → P1。

仅用 Python stdlib。用法：
  python3 mapping_fidelity.py master.tsv --col site --raw-col raw_tissue --group-by dataset_id
  python3 mapping_fidelity.py master.tsv --col site --raw-json-key regionre --json-col characteristics_json
  python3 mapping_fidelity.py --selftest
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import Issue, exit_code_for, print_issues, read_text  # noqa: E402

UNKNOWNISH = {"", "unknown", "na", "n/a", "none", "null", "nan", "unassigned", "notavailable"}


def _norm(v: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (v or "").strip().lower())


def _read_table(path: Path):
    """用 csv.reader 读——带引号/内嵌 JSON 的 TSV 用 csv/pandas 比裸 split 稳妥（嵌入分隔符/引号不易错位）。
    注：那次"site 折进 unknown"是**修前数据的真缺陷**（producer 已修），非解析假象——版本错位别甩锅给解析。"""
    import csv as _csv
    with open(path, encoding="utf-8", newline="") as f:
        first = f.readline()
        delim = "\t" if "\t" in first else ","
        f.seek(0)
        rows = list(_csv.reader(f, delimiter=delim))
    if not rows:
        return [], []
    return rows[0], rows[1:]


def _extract_json_key(cell: str, key: str) -> str:
    """从内嵌 JSON-ish 文本里抽 key 的值，容忍 TSV 转义的双引号（regionre"": ""leftcolon）。"""
    if not cell:
        return ""
    m = re.search(re.escape(key) + r"[\"'\s:=]*([A-Za-z][A-Za-z0-9_ \-]*)", cell, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def build_issues(tsv: Path, mapped_col: str, raw_col: str = "", raw_json_key: str = "",
                 json_col: str = "characteristics_json", group_by: str = "",
                 threshold: float = 0.05) -> list:
    issues = []
    header, rows = _read_table(tsv)
    if not header:
        return [Issue("P2", "MAPPING_EMPTY", f"表为空或读不出: {tsv}", str(tsv))]
    if mapped_col not in header:
        return [Issue("P2", "MAPPING_COL_ABSENT", f"mapped 列 {mapped_col} 不在表头", str(tsv))]
    mi = header.index(mapped_col)
    ri = header.index(raw_col) if raw_col and raw_col in header else -1
    ji = header.index(json_col) if raw_json_key and json_col in header else -1
    gi = header.index(group_by) if group_by and group_by in header else -1
    if ri < 0 and ji < 0:
        return [Issue("P2", "MAPPING_RAW_ABSENT",
                      f"raw 来源缺失（--raw-col {raw_col} 或 --raw-json-key {raw_json_key} 未命中）", str(tsv))]

    def cell(parts, idx):
        return parts[idx].strip() if 0 <= idx < len(parts) else ""

    # 聚合
    groups = {}   # gkey -> dict(n, raw_present, collapsed, raw_cats set, mapped_cats set, collapsed_cats set)
    for parts in rows:
        gkey = cell(parts, gi) if gi >= 0 else "ALL"
        raw_val = _extract_json_key(cell(parts, ji), raw_json_key) if ji >= 0 else cell(parts, ri)
        mapped_val = cell(parts, mi)
        raw_present = _norm(raw_val) not in UNKNOWNISH
        mapped_known = _norm(mapped_val) not in UNKNOWNISH
        g = groups.setdefault(gkey, dict(n=0, raw_present=0, collapsed=0,
                                         raw_cats=set(), mapped_cats=set(), collapsed_cats=set()))
        g["n"] += 1
        if mapped_known:
            g["mapped_cats"].add(_norm(mapped_val))
        if raw_present:
            g["raw_present"] += 1
            g["raw_cats"].add(_norm(raw_val))
            if not mapped_known:
                g["collapsed"] += 1
                g["collapsed_cats"].add(_norm(raw_val))

    total_collapsed = 0
    for gkey, g in sorted(groups.items()):
        if g["raw_present"] == 0:
            continue
        rate = g["collapsed"] / g["raw_present"]
        total_collapsed += g["collapsed"]
        # 整类被丢：raw 出现过、但从没进 mapped 词表
        dropped = sorted(c for c in g["raw_cats"] if c and c not in g["mapped_cats"])
        if g["collapsed"] and rate > threshold:
            issues.append(Issue(
                "P1", "MAPPING_SILENT_COLLAPSE",
                f"[{gkey}] {g['collapsed']}/{g['raw_present']} 行 raw 有值却 mapped={mapped_col}=unknown/空 "
                f"(折进率 {rate:.1%}>阈值 {threshold:.0%})；折进类别: {sorted(g['collapsed_cats'])[:8]}",
                f"{tsv}:{mapped_col}",
                hint="回溯 RAW 源字段补映射，或如实披露该 %unknown 的成因与下游影响（勿静默）",
            ))
        if dropped:
            issues.append(Issue(
                "P1", "MAPPING_VOCAB_DROPPED",
                f"[{gkey}] raw 里有但 {mapped_col} 从不出现的类别(整类静默丢): {dropped[:10]}",
                f"{tsv}:{mapped_col}",
                hint="这些类别在受控词表里存在却没被映射进去——补映射或披露",
            ))

    issues.append(Issue(
        "INFO", "MAPPING_FIDELITY",
        f"{mapped_col}: 分组 {len(groups)}，总折进 {total_collapsed} 行（raw 有值却 mapped 空）",
        str(tsv), hint="docs/SHARED-AUDIT.md §7 · raw-保真优于自洽",
    ))
    return issues


def _selftest() -> int:
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        # 复现 GSE193677：raw regionre=LeftColon/RightColon，但 mapped site=unknown
        f = Path(td) / "master.tsv"
        lines = ["dataset_id\tsite\tcharacteristics_json"]
        for i in range(180):
            lines.append('GSE193677\tunknown\t{regionre"": ""LeftColon""}')
        for i in range(252):
            lines.append('GSE193677\tunknown\t{regionre"": ""RightColon""}')
        for i in range(100):
            lines.append('GSE193677\trectum\t{regionre"": ""Rectum""}')
        f.write_text("\n".join(lines), encoding="utf-8")

        issues = build_issues(f, mapped_col="site", raw_json_key="regionre",
                              json_col="characteristics_json", group_by="dataset_id")
        codes = [i.code for i in issues]
        assert "MAPPING_SILENT_COLLAPSE" in codes, "应抓到 432 折进"
        assert "MAPPING_VOCAB_DROPPED" in codes, "leftcolon/rightcolon 整类被丢应报"
        assert any(i.severity == "P1" for i in issues), "折进应 P1"
        # rectum 进了 mapped，不应被算作 dropped
        dropped_msg = " ".join(i.message for i in issues if i.code == "MAPPING_VOCAB_DROPPED")
        assert "rectum" not in dropped_msg, "已正确映射的 rectum 不该报丢"
        assert "leftcolon" in dropped_msg and "rightcolon" in dropped_msg
        print("selftest PASS:", codes)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="受控词表 raw→mapped 保真度检查")
    ap.add_argument("tsv", nargs="?", default="", help="要查的表（TSV/CSV）")
    ap.add_argument("--col", required=False, help="mapped 受控词表列，如 site")
    ap.add_argument("--raw-col", default="", help="raw 来源列")
    ap.add_argument("--raw-json-key", default="", help="从内嵌 JSON 列抽的 key，如 regionre")
    ap.add_argument("--json-col", default="characteristics_json", help="内嵌 JSON 所在列名")
    ap.add_argument("--group-by", default="", help="分组列，如 dataset_id")
    ap.add_argument("--threshold", type=float, default=0.05, help="折进率告警阈值")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return _selftest()
    if not args.tsv or not args.col:
        ap.error("需要 <tsv> 和 --col（或 --selftest）")
    issues = build_issues(Path(args.tsv), args.col, args.raw_col, args.raw_json_key,
                          args.json_col, args.group_by, args.threshold)
    print_issues(issues, args.json)
    return exit_code_for(issues, args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
