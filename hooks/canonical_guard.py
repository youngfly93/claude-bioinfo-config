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
# "又复制了一份 / 新版本"的文件名特征（只对新建文件名判定，防多版本 md 堆叠）
COPY = re.compile(
    r"副本|备份|_v\d|_final\b|_最终|_定稿|"
    r"\(\d+\)|（\d+）|"
    r"[ _\-](copy|bak|backup|old|new)\b|\.bak\b|"
    r"_新|_旧",
    re.IGNORECASE)
# Bash 里的"会改东西"的动作（光 ls/cat/grep 这些读操作不警告）
MUTATE = re.compile(r"\b(rm|mv|cp|truncate|tee|dd)\b|>>?\s*(?!/dev/null\b)(?!&)\S")


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return
    tool = data.get("tool_name", "")
    ti = data.get("tool_input", {})

    DIR_MSG = ("⚠️ 目标在「非正本目录」（.tmp* / 旧版本 _v* / _archive / 副本）。"
               "确认这是不是你要改/删的正本——别在临时或旧版本目录里改正事、删数据前先看清内容"
               "（交付纪律：只在正本目录改）。确实要继续就批准。")
    COPY_MSG = ("⚠️ 这个文件名像「又复制一份 / 新版本」（副本 / copy / (2) / _v* / _final / _new 等）。"
                "多版本 md 是误解的头号来源——优先**改原来那个文件**，版本变更交给 git，别靠文件名堆版本。"
                "确为有意另存新版就批准。")

    reason = None
    if tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        path = ti.get("file_path") or ti.get("notebook_path") or ""
        if BAD.search(path):
            reason = DIR_MSG
        elif COPY.search(path):          # 只对新建/写入的文件名判多版本，精准、无 Bash 误伤
            reason = COPY_MSG
    elif tool == "Bash":
        cmd = ti.get("command", "")
        # 命令里既有"改东西"的动作、又点到非正本路径 → 警告
        if MUTATE.search(cmd) and BAD.search(cmd):
            reason = DIR_MSG
    else:
        return

    if reason:
        json.dump({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": reason,
            }
        }, sys.stdout)


if __name__ == "__main__":
    main()
