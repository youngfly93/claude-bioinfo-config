#!/usr/bin/env python3
"""双 agent 共享审计核对——别靠肉眼比 Claude / Codex 的审计。

读项目 `audit/<module>.<agent>.md`（标准见 docs/SHARED-AUDIT.md），对每个 module：
  1. 两边是否审了【同一个 commit】——不同 → 响亮报错（这就是"说的不是一个事儿"被当场抓住）；
  2. 覆盖缺口——某 module 只有一边审了；
  3. 按 finding id 并排两边 verdict，标出 ✅一致 / ⚠️分歧，让人只盯真正要裁的。

只读。退出码 = commit 不一致的 module 数（0 = 没有"两个事儿"）；覆盖缺口/verdict 分歧
是信息（那正是要人看的，不算失败）。

用法：
  python3 harness/lib/audit_reconcile.py <项目根|audit目录>
  python3 harness/lib/audit_reconcile.py --selftest
"""
import os
import re
import sys

FNAME = re.compile(r"^(?P<module>.+)\.(?P<agent>claude|codex)\.md$")
FM_KEY = lambda k: re.compile(rf"^{k}:\s*(.+?)\s*$", re.M)  # noqa: E731
ROW = re.compile(r"^\s*\|(.+)\|\s*$")


def _frontmatter(text):
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    fm = text[3:end] if end != -1 else ""
    out = {}
    for k in ("module", "agent", "audited_commit"):
        m = FM_KEY(k).search(fm)
        if m:
            out[k] = m.group(1).strip()
    return out


def _findings(text):
    """解析发现表 → {id: verdict}。跳过表头/分隔行。"""
    out = {}
    for line in text.splitlines():
        m = ROW.match(line)
        if not m:
            continue
        cells = [c.strip() for c in m.group(1).split("|")]
        if len(cells) < 5:
            continue
        fid, verdict = cells[0], cells[-1]
        if fid.lower() == "id" or set(fid) <= set("-: "):
            continue                      # 表头 | 分隔行
        if fid:
            out[fid] = verdict
    return out


def load(audit_dir):
    """返回 {module: {agent: {commit, findings, file}}}。"""
    mods = {}
    for f in sorted(os.listdir(audit_dir)):
        m = FNAME.match(f)
        if not m:
            continue
        text = open(os.path.join(audit_dir, f), encoding="utf-8").read()
        fm = _frontmatter(text)
        module = m.group("module")        # 以文件名为准（防 frontmatter 写歪）
        agent = m.group("agent")
        mods.setdefault(module, {})[agent] = {
            "commit": fm.get("audited_commit", ""),
            "findings": _findings(text),
            "file": f,
        }
    return mods


def reconcile(audit_dir):
    """返回 (lines, mismatch_count)。"""
    lines, mismatch = [], 0
    if not os.path.isdir(audit_dir):
        return [f"无 audit 目录：{audit_dir}"], 0
    mods = load(audit_dir)
    if not mods:
        return [f"audit 目录无 <module>.<agent>.md 文件：{audit_dir}"], 0

    for module in sorted(mods):
        per = mods[module]
        lines.append(f"\n## {module}")
        if len(per) < 2:
            only = next(iter(per))
            lines.append(f"  ⚠️ 覆盖缺口：只有 {only} 审了（缺 {'codex' if only=='claude' else 'claude'}）")
            continue
        c_commit = per["claude"]["commit"]
        x_commit = per["codex"]["commit"]
        if c_commit != x_commit:
            mismatch += 1
            lines.append(f"  ⛔ 不是一个事儿：claude 审 {c_commit or '?'} / codex 审 {x_commit or '?'} —— 审的不是同一版，先对齐 commit 再比")
            continue
        lines.append(f"  审同一版 commit={c_commit or '?'}")
        ids = sorted(set(per["claude"]["findings"]) | set(per["codex"]["findings"]))
        if not ids:
            lines.append("  （两边都无 finding）")
        for fid in ids:
            cv = per["claude"]["findings"].get(fid)
            xv = per["codex"]["findings"].get(fid)
            if cv is None:
                lines.append(f"  ⚠️ {fid}: 仅 codex 提（{xv}）——claude 漏了或不认")
            elif xv is None:
                lines.append(f"  ⚠️ {fid}: 仅 claude 提（{cv}）——codex 漏了或不认")
            elif cv == xv:
                lines.append(f"  ✅ {fid}: 一致（{cv}）")
            else:
                lines.append(f"  ⚠️ {fid}: 分歧 claude={cv} / codex={xv} —— 要裁")
    return lines, mismatch


def main(argv):
    if argv and argv[0] == "--selftest":
        return _selftest()
    root = argv[0] if argv else "."
    audit_dir = root if os.path.basename(os.path.normpath(root)) == "audit" else os.path.join(root, "audit")
    lines, mismatch = reconcile(audit_dir)
    print(f"# 双 agent 审计核对 · {audit_dir}")
    print("\n".join(lines))
    print(f"\n{'⛔' if mismatch else '✅'} commit 不一致的 module：{mismatch}")
    return mismatch


def _selftest():
    import tempfile
    import shutil
    d = tempfile.mkdtemp(prefix="auditrec_")
    a = os.path.join(d, "audit")
    os.makedirs(a)
    try:
        def w(fn, commit, rows):
            body = "---\nmodule: %s\nagent: %s\naudited_commit: %s\n---\n" % (
                fn.split(".")[0], fn.split(".")[1], commit)
            body += "| id | severity | claim | evidence | verdict |\n|---|---|---|---|---|\n"
            for fid, v in rows:
                body += f"| {fid} | P1 | c | e | {v} |\n"
            open(os.path.join(a, fn), "w", encoding="utf-8").write(body)

        # m1: 同 commit，一条一致一条分歧
        w("m1.claude.md", "aaa", [("m1-01", "CONFIRMED"), ("m1-02", "CONFIRMED")])
        w("m1.codex.md", "aaa", [("m1-01", "CONFIRMED"), ("m1-02", "REFUTED")])
        # m2: 不同 commit → 必须当 mismatch 抓住
        w("m2.claude.md", "aaa", [("m2-01", "CONFIRMED")])
        w("m2.codex.md", "bbb", [("m2-01", "CONFIRMED")])
        # m3: 只有一边 → 覆盖缺口
        w("m3.claude.md", "aaa", [("m3-01", "CONFIRMED")])

        lines, mismatch = reconcile(a)
        text = "\n".join(lines)
        checks = {
            "m2 commit 不一致被抓": mismatch == 1 and "不是一个事儿" in text,
            "m1-02 分歧被标": "m1-02: 分歧" in text,
            "m1-01 一致被标": "m1-01: 一致" in text,
            "m3 覆盖缺口被标": "覆盖缺口" in text,
        }
        bad = [k for k, ok in checks.items() if not ok]
        if bad:
            print("selftest FAIL：", bad)
            print(text)
            return 1
        print("selftest: OK（commit 不一致/分歧/一致/覆盖缺口 全部正确识别）")
        return 0
    finally:
        shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
