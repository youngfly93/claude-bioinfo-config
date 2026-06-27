#!/usr/bin/env python3
"""
Claude Code PreToolUse hook：检测"用 shell 重定向把中文写进文件"的高风险写法
（echo/cat/printf ...中文... > 文件 / 含中文的 heredoc 写文件），提醒改用
Python 显式 UTF-8 写文件。这是用户使用报告里的头号报错来源（CJK 经 shell 乱码）。

刻意保守，只在"中文 + 写文件重定向"同时出现时才警告：
  - 不报：echo "中文"（仅 stdout）、grep 中文 file、ls 中文目录、> /dev/null、>&2
  - 报：  echo "中文" > a.txt / cat > a.md <<EOF ...中文... EOF / printf "中文" >> log
"""
import sys
import json
import re

CJK = r'[㐀-䶿一-鿿豈-﫿]'


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    if data.get("tool_name", "") != "Bash":
        return
    command = data.get("tool_input", {}).get("command", "")
    if not command or not re.search(CJK, command):
        return  # 无中文 → 不管

    # 写文件重定向（排除 /dev/null 和 >&fd）
    writes_file = re.search(r'>>?\s*(?!/dev/null\b)(?!&)\S', command)
    # heredoc 同时写文件： cat > file <<EOF
    heredoc_to_file = ('<<' in command) and re.search(r'>\s*[^<\s]', command)

    if not (writes_file or heredoc_to_file):
        return  # 中文只是参数/搜索词，不写文件 → 不管

    result = {
        "decision": "warn",
        "reason": (
            "⚠️ 检测到用 shell 重定向把中文写进文件（echo/cat/printf/heredoc > 文件）。"
            "shell 在部分 locale 下会弄乱中文编码，是高频报错来源。"
            "建议改用 Python 显式写：with open(path,'w',encoding='utf-8') as f: f.write(...)。"
        ),
    }
    json.dump(result, sys.stdout)


if __name__ == "__main__":
    main()
