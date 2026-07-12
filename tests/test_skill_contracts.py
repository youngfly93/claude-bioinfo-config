#!/usr/bin/env python3
"""skill 契约 lint：机械体检 skill/agent/workflow/command 的**硬不变量**。

把"公开 skill 别读运行态历史""name 要对得上目录"这类错，从靠人工阅读升级成
可执行保证（同坏案例 fixture 哲学）。**只放客观、零/极低误报的不变量**——不编码
风格意见（description 长度、要不要 disable-model-invocation 这类都不进），免得 lint
自己变成噪音被忽略。

- 检查1 NAME_MISMATCH：skills/<X>/SKILL.md 的 frontmatter name 必须 == 父目录名。
- 检查2 READS_RUNTIME_STATE：任何 prompt 面都不得读 Claude/Codex 运行态历史
  （对齐 AGENTS.md「不读取/复制 history.jsonl / sessions / file-history …」；
  历史里常含客户名/本机路径/样本名/未脱敏数据——公开 skill 读它是隐私红线）。
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# AGENTS.md 明列的运行态历史文件/目录——出现在 prompt 面即违规（habit-analyzer 那类）。
FORBIDDEN_RUNTIME = ["history.jsonl", "sessions/", "file-history", "paste-cache", "shell-snapshots"]


def frontmatter_name(text):
    m = re.search(r"^---\s*$(.*?)^---\s*$", text, re.S | re.M)
    if not m:
        return None
    nm = re.search(r"^name:\s*(.+?)\s*$", m.group(1), re.M)
    return nm.group(1).strip() if nm else None


def prompt_surface():
    files = []
    files += sorted(ROOT.glob("skills/*/SKILL.md"))
    files += sorted(ROOT.glob("agents/*.md"))
    files += sorted(ROOT.glob("workflows/*.js"))
    files += sorted(ROOT.glob("commands/*.md"))
    return files


def main():
    problems = []
    # 检查1：name == 目录名
    for f in sorted(ROOT.glob("skills/*/SKILL.md")):
        nm = frontmatter_name(f.read_text(encoding="utf-8"))
        d = f.parent.name
        if nm is None:
            problems.append(f"[NAME_MISSING]  {f.relative_to(ROOT)}：缺 frontmatter name:")
        elif nm != d:
            problems.append(f"[NAME_MISMATCH] {f.relative_to(ROOT)}：name={nm} ≠ 目录 {d}")
    # 检查2：不读运行态历史
    for f in prompt_surface():
        t = f.read_text(encoding="utf-8", errors="ignore")
        for tok in FORBIDDEN_RUNTIME:
            if tok in t:
                problems.append(
                    f"[READS_RUNTIME_STATE] {f.relative_to(ROOT)}：含 '{tok}'——违反 AGENTS.md「不读运行态历史」")

    print("== skill 契约 lint（硬不变量）==")
    for p in problems:
        print(f"  ✗ {p}")
    if problems:
        print(f"skill contracts: FAIL（{len(problems)} 处违规）")
        return 1
    print("skill contracts: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
