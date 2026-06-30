#!/usr/bin/env python3
"""Claude Code PreToolUse hook：不可逆破坏操作减速带。

拦截那些会**静默吃掉未提交工作 / 改写远端历史**的命令——执行前弹给用户确认
（permissionDecision=ask，不硬阻断），把"别擅自做不可逆操作"从自觉变成机械减速带。
保守：只点名公认不可逆的几条，正常操作（push、reset --soft、clean -n、branch -d、
checkout 分支名、restore 单个文件）一律放行，宁可漏报不误伤。

设计取舍：
- 用 ask 不用 deny——你仍是最终闸门，确为有意就批准；真要绕过可在 prompt 用 `!` 前缀
  自己跑（那走你的 shell，不经 agent 的 Bash 工具，不触发本钩子）。
- 不拦普通 `git push`（你授权了就推）；只拦 `--force` 改写远端历史。
- 不拦通用 `rm -rf`——太常见会噪声爆炸（含清 scratchpad），交给 canonical_guard 的
  非正本目录提醒覆盖；要拦特定结果目录再单独加。

借鉴 mattpocock/skills 的 git-guardrails（裁剪：放行 push、改 deny 为 ask、对齐 house 风格）。
"""
import sys
import json
import re

# 每条：(正则, 为什么危险)。大小写敏感——-D 危险、-d 安全，必须区分。
# [^&|;]* 限定在同一命令段内匹配，防跨 && / ; 误判。
RULES = [
    (re.compile(r"\bgit\s+reset\b[^&|;]*\s--hard\b"),
     "git reset --hard 丢弃所有未提交改动，不可逆"),
    (re.compile(r"\bgit\s+clean\b[^&|;]*\s-[A-Za-z]*f"),
     "git clean -f 删除未跟踪文件（可能含结果/数据），不可逆"),
    (re.compile(r"\bgit\s+checkout\b[^&|;]*?\s(--\s+)?\.(\s|$)"),
     "git checkout . 丢弃工作区全部改动，不可逆"),
    (re.compile(r"\bgit\s+checkout\b[^&|;]*\s(-f|--force)\b"),
     "git checkout -f 强制覆盖工作区改动，不可逆"),
    (re.compile(r"\bgit\s+restore\b[^&|;]*?\s\.(\s|$)"),
     "git restore . 丢弃工作区全部改动，不可逆"),
    (re.compile(r"\bgit\s+branch\b[^&|;]*\s-D\b"),
     "git branch -D 强删未合并分支，可能丢提交"),
    (re.compile(r"\bgit\s+stash\s+(clear|drop)\b"),
     "git stash clear/drop 丢弃暂存的工作，不可逆"),
    (re.compile(r"\bgit\s+push\b[^&|;]*\s(-f|--force)"),
     "git push --force 改写远端历史（canonical 是单一真源），危险"),
]


def check(cmd):
    """返回命中的危险说明列表（可能多条）。"""
    return [why for rx, why in RULES if rx.search(cmd)]


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return
    if data.get("tool_name", "") != "Bash":
        return
    cmd = data.get("tool_input", {}).get("command", "")
    hits = check(cmd)
    if not hits:
        return

    reason = ("⛔ 检测到不可逆破坏操作：\n  - " + "\n  - ".join(hits) +
              "\n确为有意（且已确认无未提交工作要保留）就批准；"
              "否则先 git status/stash 保住现场。真要绕过可在 prompt 用 `!` 前缀自己跑。")
    json.dump({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    }, sys.stdout)


def _selftest():
    block = [
        "git reset --hard",
        "git reset --hard HEAD~3",
        "cd repo && git reset --hard origin/main",
        "git clean -fd",
        "git clean -xfd",
        "git clean -f",
        "git checkout .",
        "git checkout -- .",
        "git checkout -f",
        "git restore .",
        "git branch -D feature",
        "git stash clear",
        "git stash drop",
        "git push --force",
        "git push -f origin main",
        "git push --force-with-lease",
    ]
    allow = [
        "git reset --soft HEAD~1",
        "git reset HEAD file.txt",
        "git clean -n",
        "git clean -dn",
        "git checkout main",
        "git checkout -b newbranch",
        "git checkout feature/x",
        "git restore --staged file.txt",
        "git branch -d merged-branch",
        "git push origin main",
        "git status",
        "git commit -m 'wip'",
        "git stash",
        "git stash pop",
    ]
    bad = 0
    for c in block:
        if not check(c):
            print(f"  FAIL 该拦没拦: {c}")
            bad += 1
    for c in allow:
        h = check(c)
        if h:
            print(f"  FAIL 误伤正常: {c} -> {h}")
            bad += 1
    if bad:
        print(f"selftest: {bad} 例失败")
        sys.exit(1)
    print(f"selftest: OK（拦 {len(block)} / 放行 {len(allow)}）")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        _selftest()
    else:
        main()
