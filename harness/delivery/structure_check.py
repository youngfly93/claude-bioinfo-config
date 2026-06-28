#!/usr/bin/env python3
"""交付目录结构校验：把 bio-deliver 的「标准结构」从散文规范变成机器 gate，
保证客户拿到的包结构清晰一致、好找。stdlib only。

severity:
- P1（默认即拦,exit 1）：放错位置——图/ 里混进表、表/ 里混进图、根本没有报告。
- P2（建议,--strict 才拦）：无 01_分析报告/、主题夹没分 图/表、根目录有散文件。
- P3：缺溯源表/导航、编号跳号。
设计上对"小项目/非标准布局"宽容(只软提示)，只在明确摆错时硬拦。
"""
import os, sys, json

EXCLUDE = {".DS_Store", "__MACOSX", ".git", ".bio_harness", "proof.json", "goal_proof.md"}
IMG_EXT = {".png", ".pdf", ".tiff", ".tif", ".jpg", ".jpeg", ".svg", ".eps"}
TABLE_EXT = {".csv", ".tsv", ".xlsx", ".xls"}


def _is_tu(name):
    return "图" in name or name.lower() in ("figures", "fig", "figure")


def _is_biao(name):
    return "表" in name or name.lower() in ("tables", "table")


def run(root):
    # 若 delivery/ 下只有一个子夹(项目交付夹)、无散文件,下钻进它(对齐 zip_pack 单一根逻辑)
    top = [e for e in os.listdir(root) if not e.startswith(".") and e not in EXCLUDE]
    tsd = [e for e in top if os.path.isdir(os.path.join(root, e))]
    tlf = [e for e in top if os.path.isfile(os.path.join(root, e))]
    if len(tsd) == 1 and not tlf:
        root = os.path.join(root, tsd[0])

    F = []
    def add(sev, code, msg, where=""):
        F.append({"severity": sev, "code": code, "message": msg, "path": where or os.path.basename(root)})

    entries = [e for e in os.listdir(root) if not e.startswith(".") and e not in EXCLUDE]
    dirs = sorted(d for d in entries if os.path.isdir(os.path.join(root, d)))
    files = [f for f in entries if os.path.isfile(os.path.join(root, f))]

    # 报告存在
    has_report = (any("报告" in d or "report" in d.lower() for d in dirs)
                  or any(f.lower().endswith((".docx", ".pdf")) for f in files))
    if not has_report:
        add("P2", "NO_REPORT", "未见分析报告（建议放 01_分析报告/）")

    # 根目录散文件（除 00_* 导航/说明、溯源表）
    for f in files:
        if not (f.startswith("00_") or "溯源" in f):
            add("P2", "STRAY_ROOT_FILE", f"根目录散落文件，建议归入主题/报告/代码夹：{f}", f)

    # 主题夹：图/表 分离 + 内容放对位置
    theme_dirs = [d for d in dirs if d[:2].isdigit() and d[:2] not in ("00", "01")
                  and "代码" not in d and "script" not in d.lower()]
    for d in theme_dirs:
        dp = os.path.join(root, d)
        subs = [s for s in os.listdir(dp) if os.path.isdir(os.path.join(dp, s))]
        loose = [f for f in os.listdir(dp) if os.path.isfile(os.path.join(dp, f)) and not f.startswith(".")]
        if not any(_is_tu(s) or _is_biao(s) for s in subs) and loose:
            add("P2", "THEME_NO_TU_BIAO", f"主题夹未分 图/表（图表混放）：{d}", d)
        for s in subs:
            sp = os.path.join(dp, s)
            fs = [f for f in os.listdir(sp) if os.path.isfile(os.path.join(sp, f)) and not f.startswith(".")]
            if _is_tu(s):
                bad = [f for f in fs if os.path.splitext(f)[1].lower() in TABLE_EXT]
                if bad:
                    add("P1", "IMG_DIR_HAS_TABLE", f"「图/」里混进了表（{d}/{s}）：{bad[:3]}", f"{d}/{s}")
            if _is_biao(s):
                bad = [f for f in fs if os.path.splitext(f)[1].lower() in IMG_EXT]
                if bad:
                    add("P1", "TABLE_DIR_HAS_IMG", f"「表/」里混进了图（{d}/{s}）：{bad[:3]}", f"{d}/{s}")

    # 溯源表 / 导航
    if not any("溯源" in e for e in entries):
        add("P3", "NO_TRACE_TABLE", "未见溯源表（建议 NN_溯源表.xlsx）")
    if "00_目录导航.md" not in files:
        add("P3", "NO_INDEX", "未见 00_目录导航.md（用 make_index.py 生成）")

    # 编号跳号
    nums = sorted({int(d[:2]) for d in dirs if d[:2].isdigit()})
    if nums:
        missing = [n for n in range(nums[0], nums[-1] + 1) if n not in nums]
        if missing:
            add("P3", "NUMBERING_GAP", f"主题编号跳号：缺 {missing}")
    return F


def main():
    args = [a for a in sys.argv[1:] if a != "--strict"]
    strict = "--strict" in sys.argv
    target = os.path.abspath(args[0] if args else "delivery")
    findings = run(target)
    print(json.dumps(findings, ensure_ascii=False, indent=2))
    fail = {"P0", "P1", "P2"} if strict else {"P0", "P1"}
    bad = [x for x in findings if x["severity"] in fail]
    if bad:
        print(f"structure_check: {len(bad)} 处需处理（{'含 P2' if strict else 'P1 摆错位置'}）。", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
