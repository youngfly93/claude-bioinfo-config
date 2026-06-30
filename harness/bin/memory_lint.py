#!/usr/bin/env python3
"""Claude 记忆/知识库体检（memory lint）——只读、只标记、不自动改。

借鉴 karpathy llm-wiki 的 "lint" 工作流：知识库是会复利累积的持久产物，要定期体检
防腐化。本仓的 memory 系统（MEMORY.md 索引 + 每条 memory 一个 .md + `[[name]]` 交叉引用）
正是 llm-wiki 的 index.md + 实体页 + wikilink，唯独缺这道体检——补上。

检查项（对齐 harness 的 P0-P3 口径；本工具最高到 P1，是卫生不是交付阻断）：
  P1 索引说谎    MEMORY.md 指向的 .md 不存在（index 是唯一发现入口，断链最伤）
  P2 孤儿文件    memory 的 .md 存在却没进 MEMORY.md 索引（会被遗忘）
  P2 缺 name     memory 文件 frontmatter 没有 name: （[[链接]]靠它寻址）
  P3 name 不符   name: 与文件名不一致（建议同名，便于 [[链接]] 对应）
  P3 悬空链接    正文 [[xxx]] 找不到对应 memory（可能是该写的新条目，也可能是笔误）
  P3 过期路径    反引号里的绝对/~路径在磁盘上不存在（对应 memory 指令"引用前先核实仍存在"）

只标记不改：发现归发现，怎么处理由你定（跟 bio-result-auditor 一个调性）。
退出码 = P1 条数（0 = 无硬断链）。

用法：
  python3 harness/bin/memory_lint.py [MEMORY_DIR]    # 不给则从 cwd 自动推导
  python3 harness/bin/memory_lint.py --selftest
"""
import sys
import os
import re

FM_NAME = re.compile(r"^name:\s*(.+?)\s*$", re.M)
INDEX_LINK = re.compile(r"^- \[[^\]]*\]\(([^)]+\.md)\)", re.M)
WIKILINK = re.compile(r"\[\[([^\]\[]+)\]\]")
BACKTICK = re.compile(r"`([^`]+)`")
# 路径起点的 ~// 前面不能是字母/数字/._-，否则是相对路径的中段斜杠（scratchpad/x.py
# 里的 /x.py）或词内斜杠（owner/repo 里的 /repo），不是绝对路径起点。
PATH_TOKEN = re.compile(r"(?<![A-Za-z0-9_.\-])(?:~|/)[A-Za-z0-9_.~/\-]+")


def default_memory_dir():
    """Claude Code 把 memory 目录按 cwd 编码：/a/b → -a-b。"""
    enc = os.getcwd().replace("/", "-")
    return os.path.expanduser(f"~/.claude/projects/{enc}/memory")


def parse_frontmatter(text):
    """返回 (name 或 None, body)。frontmatter 是开头两个 --- 之间的块。"""
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end == -1:
        return None, text
    fm = text[3:end]
    body = text[end + 4:]
    m = FM_NAME.search(fm)
    return (m.group(1).strip() if m else None), body


def candidate_path(tok):
    """把一个 token 归一成"该核实的本地路径"，不像就返回 None（保守、避免误报）。"""
    tok = tok.strip().rstrip(".,;:)]}\"'`")
    if not tok.startswith(("/", "~")):
        return None              # 相对路径相对 cwd 不定，跳过
    if "/" not in tok:
        return None
    if "..." in tok or "…" in tok:
        return None              # 省略号示例路径（source("~/.claude/...")）
    if "://" in tok:
        return None              # URL
    if any(c in tok for c in "<>*$ \t"):
        return None              # 占位符 / 变量 / 含空格
    if tok.count("/") < 2 and not tok.startswith("~"):
        return None              # 单段 /plugin /save 多是斜杠命令，不是路径
    return tok


def lint(mdir):
    """返回 findings: [(severity, code, msg)]，severity ∈ {P1,P2,P3}。"""
    findings = []
    if not os.path.isdir(mdir):
        return [("P1", "NO_MEMORY_DIR", f"memory 目录不存在：{mdir}")]

    index_path = os.path.join(mdir, "MEMORY.md")
    md_files = sorted(
        f for f in os.listdir(mdir)
        if f.endswith(".md") and f != "MEMORY.md"
    )

    # 解析每个 memory 文件
    names = {}          # filename -> name(frontmatter)
    bodies = {}         # filename -> body
    for f in md_files:
        text = open(os.path.join(mdir, f), encoding="utf-8").read()
        name, body = parse_frontmatter(text)
        names[f] = name
        bodies[f] = body
        if not name:
            findings.append(("P2", "NO_NAME", f"{f}: frontmatter 缺 name:（[[链接]]靠它寻址）"))
        elif name != f[:-3]:
            findings.append(("P3", "NAME_MISMATCH",
                             f"{f}: name='{name}' 与文件名不一致（建议同名）"))

    # 已知 slug 集合（name 优先，回退文件名）
    known_slugs = {(names[f] or f[:-3]) for f in md_files}

    # 索引 ↔ 文件 一致性
    if not os.path.exists(index_path):
        findings.append(("P1", "NO_INDEX", "缺 MEMORY.md 索引（唯一发现入口）"))
        indexed = set()
    else:
        index_text = open(index_path, encoding="utf-8").read()
        indexed = set(INDEX_LINK.findall(index_text))
        for target in sorted(indexed):
            if not os.path.exists(os.path.join(mdir, target)):
                findings.append(("P1", "BROKEN_POINTER",
                                 f"MEMORY.md 指向不存在的文件：{target}"))
    for f in md_files:
        if f not in indexed:
            findings.append(("P2", "ORPHAN_FILE",
                             f"{f}: 存在却没进 MEMORY.md 索引（会被遗忘）"))

    # 悬空 [[wikilink]] + 过期路径（逐文件扫正文）
    for f in md_files:
        body = bodies[f]
        for link in WIKILINK.findall(body):
            slug = link.strip()
            if slug and slug not in known_slugs:
                findings.append(("P3", "DANGLING_LINK",
                                 f"{f}: [[{slug}]] 无对应 memory（待写的新条目？还是笔误？）"))
        seen = set()
        for span in BACKTICK.findall(body):
            for raw in PATH_TOKEN.findall(span):
                p = candidate_path(raw)
                if not p or p in seen:
                    continue
                seen.add(p)
                if not os.path.exists(os.path.expanduser(p)):
                    findings.append(("P3", "STALE_PATH",
                                     f"{f}: 引用的路径不存在（核实）：`{p}`"))

    return findings


def report(mdir, findings):
    order = {"P1": 0, "P2": 1, "P3": 2}
    findings = sorted(findings, key=lambda x: order.get(x[0], 9))
    n = {"P1": 0, "P2": 0, "P3": 0}
    for sev, _, _ in findings:
        n[sev] = n.get(sev, 0) + 1

    print(f"# memory lint · {mdir}\n")
    if not findings:
        print("✅ 干净：索引一致、无孤儿、无悬空链接、无过期路径。")
        return 0
    print(f"发现 {len(findings)} 项：P1={n['P1']} · P2={n['P2']} · P3={n['P3']}"
          "（P1=索引断链需修；P2=卫生；P3=建议/待核实，可能有误报）\n")
    last = None
    for sev, code, msg in findings:
        if sev != last:
            print(f"\n## {sev}")
            last = sev
        print(f"- [{code}] {msg}")
    return n["P1"]


def _selftest():
    import tempfile
    import shutil
    d = tempfile.mkdtemp(prefix="memlint_")
    try:
        def w(fn, s):
            open(os.path.join(d, fn), "w", encoding="utf-8").write(s)

        w("MEMORY.md",
          "# Memory Index\n\n"
          "- [Good](good.md) — ok\n"
          "- [Gone](missing.md) — 指向不存在\n")
        w("good.md",
          "---\nname: good\ndescription: x\n---\n"
          "正文链接 [[good]] 和 [[nope]]；假路径 `/zzz/no/such.md`；"
          "相对路径 `scratchpad/rel.py` 和斜杠命令 `/plugin add` 不该误报\n")
        w("orphan.md",
          "---\nname: orphan\ndescription: y\n---\n没进索引\n")
        w("badname.md",
          "---\nname: different\ndescription: z\n---\n名不符\n")

        codes = {c for _, c, _ in lint(d)}
        expect = {"BROKEN_POINTER", "ORPHAN_FILE", "NAME_MISMATCH",
                  "DANGLING_LINK", "STALE_PATH"}
        missing = expect - codes
        # 反向：good.md 的 [[good]] 不该悬空；相对路径/斜杠命令不该判过期
        msgs = [m for _, _, m in lint(d)]
        false_pos = [m for m in msgs
                     if "[[good]]" in m or "rel.py" in m or "/plugin" in m]

        if missing:
            print(f"selftest FAIL：这些该报没报 {missing}")
            sys.exit(1)
        if false_pos:
            print(f"selftest FAIL：误报 {false_pos}")
            sys.exit(1)
        print(f"selftest: OK（命中 {sorted(expect)}，无误报）")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def main(argv):
    if argv and argv[0] == "--selftest":
        _selftest()
        return 0
    mdir = argv[0] if argv else default_memory_dir()
    return report(mdir, lint(mdir))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
