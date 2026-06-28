#!/usr/bin/env python3
"""从真实交付结构自动生成「目录导航」(00_目录导航.md)——客户一眼定位自己要的内容。
永不过时(每次按实际文件夹/文件数生成)。stdlib only。
用法: python3 make_index.py <交付根目录> [项目名]
"""
import os, sys

EXCLUDE = {".DS_Store", "__MACOSX", ".git", ".bio_harness", "proof.json", "goal_proof.md"}


def count_files(d):
    n = 0
    for _, dns, fns in os.walk(d):
        dns[:] = [x for x in dns if x not in EXCLUDE]
        n += sum(1 for f in fns if f not in EXCLUDE and not f.startswith("."))
    return n


def label_of(name):
    base = name.split("_", 1)[1] if name[:2].isdigit() and "_" in name else name  # 去 NN_ 前缀
    return base


def locate_row(name, path, has_tu, has_biao):
    lab = label_of(name)
    low = name.lower()
    if "报告" in name or "report" in low:
        return ("📄 分析报告（先看这个）", path)
    if "溯源" in name:
        return ("🔗 每个结果/数字的来源", path)
    if "代码" in name or "脚本" in name or "script" in low:
        return ("💻 分析脚本 / 复现", path)
    if "说明" in name or "导航" in name or "readme" in low:
        return None
    sub = []
    if has_tu: sub.append("图/")
    if has_biao: sub.append("表/")
    hint = f"（{' '.join(sub)}）" if sub else ""
    return (f"📁 {lab}", path + "/" + (" ".join(sub) if sub else ""))


def main():
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
    project = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(root)
    entries = sorted(e for e in os.listdir(root)
                     if e not in EXCLUDE and not e.startswith(".") and e != "00_目录导航.md")
    dirs = [e for e in entries if os.path.isdir(os.path.join(root, e))]
    files = [e for e in entries if os.path.isfile(os.path.join(root, e))]

    locate, tree = [], []
    for d in dirs:
        dp = os.path.join(root, d)
        subs = sorted(x for x in os.listdir(dp) if os.path.isdir(os.path.join(dp, x)))
        has_tu = any("图" in s or s.lower() in ("figures", "fig") for s in subs)
        has_biao = any("表" in s or s.lower() in ("tables", "table") for s in subs)
        r = locate_row(d, d, has_tu, has_biao)
        if r:
            locate.append(r)
        # tree: 主题 → 子目录(图/表)文件数，或直接文件数
        tree.append(f"- **{d}/**  （{count_files(dp)} 个文件）")
        for s in subs:
            tree.append(f"    - {s}/  （{count_files(os.path.join(dp, s))} 个）")
    # 顶层文件（交付说明 / 溯源表 等）也要能被定位到
    for fn in files:
        r = locate_row(fn, fn, False, False)
        if r:
            locate.append(r)
        tree.append(f"- {fn}")

    lines = [f"# 📦 交付导航 · {project}", "",
             "> 双击文件夹查看；**编号即建议阅读顺序**。找不到东西先看下面这张表。", "",
             "## 快速定位（想看什么 → 打开哪里）", "",
             "| 想看什么 | 打开 |", "|---|---|"]
    for what, where in locate:
        lines.append(f"| {what} | `{where}` |")
    lines += ["", "## 完整目录", ""] + tree + ["",
              "_本导航由打包流程自动生成，与实际文件一致。_"]

    out = os.path.join(root, "00_目录导航.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(out)


if __name__ == "__main__":
    main()
