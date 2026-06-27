#!/usr/bin/env python3
"""
Claude Code PreToolUse hook: 检测 bash 命令中的 bash 4+ 语法，
提醒用户 macOS 默认 /bin/bash 是 3.x 版本。
"""
import sys
import json
import re

def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    tool_name = data.get("tool_name", "")
    if tool_name != "Bash":
        return

    tool_input = data.get("tool_input", {})
    command = tool_input.get("command", "")

    if not command:
        return

    # 只检查显式使用 /bin/bash 或 bash -c 的命令
    # zsh 命令不需要警告
    uses_bash = any(p in command for p in ["/bin/bash", "bash -c", "bash <<"])

    if not uses_bash:
        return

    # Bash 4+ 语法模式
    patterns = [
        (r'\bdeclare\s+-A\b', 'declare -A (关联数组)'),
        (r'\bmapfile\b', 'mapfile'),
        (r'\breadarray\b', 'readarray'),
        (r'\$\{[^}]+,,\}', '${var,,} (小写转换)'),
        (r'\$\{[^}]+\^\^\}', '${var^^} (大写转换)'),
        (r'\$\{![^}]+\[@\]\}', '${!var[@]} (间接引用)'),
        (r'&>>', '&>> (追加重定向)'),
        (r'\|&', '|& (管道 stderr)'),
        (r'\bcoproc\b', 'coproc (协程)'),
    ]

    found = []
    for pattern, desc in patterns:
        if re.search(pattern, command):
            found.append(desc)

    if found:
        features = ", ".join(found)
        result = {
            "decision": "warn",
            "reason": f"⚠️ 检测到 bash 4+ 语法: {features}。macOS 默认 /bin/bash 是 3.2 版本，不支持这些特性。建议改用 zsh 或 /opt/homebrew/bin/bash。"
        }
        json.dump(result, sys.stdout)

if __name__ == "__main__":
    main()
