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


def _strip_heredoc_bodies(cmd):
    """去掉 heredoc 正文（<<EOF … EOF），只留命令骨架。
    正文是喂给 stdin 的数据（常含散文/中文），里面的 `>` 不是 shell 重定向，
    不该参与写文件判定；而真·写文件 `cat > f <<EOF` 的 `> f` 在骨架里仍保留。"""
    out, delim = [], None
    for line in cmd.split("\n"):
        if delim is None:
            out.append(line)
            m = re.search(r'<<-?\s*[\'"]?(\w+)[\'"]?', line)
            if m:
                delim = m.group(1)
        elif line.strip() == delim:
            delim = None
    return "\n".join(out)


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

    # 写文件重定向：`>` 须在行首或空白后（真·重定向 `cmd > file` / `cmd >file`），
    # 从而排除 `2>`(fd 前是数字)、`>&`((?!&))、以及邮箱/泛型 `<...>` 的闭合 `>`(前是字母，如 com>)；
    # /dev/null 也排除。`cat > file <<EOF` 这种真·写文件仍会命中。
    skeleton = _strip_heredoc_bodies(command)
    writes_file = re.search(r'(?:^|\s)>>?\s*(?!/dev/null\b)(?!&)\S', skeleton)

    if not writes_file:
        return  # 中文只是参数/搜索词，或仅 heredoc 喂给 stdin/Python（推荐写法）→ 不管

    json.dump({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": (
                "⚠️ 检测到用 shell 重定向把中文写进文件（echo/cat/printf/heredoc > 文件）。"
                "shell 在部分 locale 下会弄乱中文编码，是高频报错来源。"
                "建议改用 Python 显式写：with open(path,'w',encoding='utf-8') as f: f.write(...)。"
            ),
        }
    }, sys.stdout)


if __name__ == "__main__":
    main()
