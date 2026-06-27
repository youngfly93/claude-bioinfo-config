#!/usr/bin/env python3
"""
Claude Code PreToolUse hook：正本目录守护。
检测 Edit/Write/MultiEdit/Bash 是否在改/删「非正本目录」——临时目录、旧版本、
归档、副本——警告而非阻断（保守、零阻塞），把"只在正本目录改"从 skill 自觉
变成 harness 机械提醒。对应使用报告里"改了 temp 文件夹 / 误删数据"的事故。

只警告，不阻断。识别保守，宁可漏报不误伤正常工作。
"""
import sys
import json
import re

# 非正本/高风险目录特征（路径里出现即视为非正本）
BAD = re.compile(r"(\.tmp|(^|/)_archive(/|$)|dup_extracts|build_intermediates|_v\d)")
# Bash 里的"会改东西"的动作（光 ls/cat/grep 这些读操作不警告）
MUTATE = re.compile(r"\b(rm|mv|cp|truncate|tee|dd)\b|>>?\s*(?!/dev/null\b)(?!&)\S")


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return
    tool = data.get("tool_name", "")
    ti = data.get("tool_input", {})

    hit = False
    if tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        path = ti.get("file_path") or ti.get("notebook_path") or ""
        hit = bool(BAD.search(path))
    elif tool == "Bash":
        cmd = ti.get("command", "")
        # 命令里既有"改东西"的动作、又点到非正本路径 → 警告
        hit = bool(MUTATE.search(cmd) and BAD.search(cmd))
    else:
        return

    if hit:
        json.dump({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": (
                    "⚠️ 目标在「非正本目录」（.tmp* / 旧版本 _v* / _archive / 副本）。"
                    "确认这是不是你要改/删的正本——别在临时或旧版本目录里改正事、删数据前先看清内容"
                    "（交付纪律：只在正本目录改）。确实要继续就批准。"
                ),
            }
        }, sys.stdout)


if __name__ == "__main__":
    main()
