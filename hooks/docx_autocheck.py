#!/usr/bin/env python3
"""Stop hook：若 cwd 常见报告位置有刚生成(5min内)的 .docx，自动跑 docx_check，
只在有「可处理的真问题」(XML失败/图片引用不一致/markdown残留——忽略已知的
docx-js 字体未嵌入限制)时，通过 additionalContext 提醒。无则静默。
用浅层 glob 限定位置，绝不全盘 os.walk，不拖累大盘。"""
import sys
import json
import os
import time
import glob
import subprocess

CHECK = os.path.expanduser("~/.claude/skills/bio-report/scripts/docx_check.py")
# 只查这些浅层位置（报告通常落这儿），避免递归扫整个工作树
PATTERNS = ["*.docx", "reports/*.docx", "报告/*.docx", "01_*/*.docx",
            "delivery*/*.docx", "delivery*/*/*.docx", "*/reports/*.docx"]


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    cwd = data.get("cwd") or os.getcwd()
    if (not cwd or not os.path.isdir(cwd)
            or os.path.realpath(cwd) == os.path.realpath(os.path.expanduser("~"))):
        return
    if not os.path.exists(CHECK):
        return

    now = time.time()
    found = set()
    for pat in PATTERNS:
        for p in glob.glob(os.path.join(cwd, pat)):
            if os.path.basename(p).startswith("~$"):
                continue
            try:
                if now - os.path.getmtime(p) < 300:  # 5 分钟内生成的
                    found.add(p)
            except OSError:
                pass
    if not found:
        return

    msgs = []
    for p in list(found)[:5]:
        try:
            r = subprocess.run(["python3", CHECK, "check", p],
                               capture_output=True, text=True, timeout=15)
            o = json.loads(r.stdout) if r.stdout.strip() else {}
            fails = o.get("fail", [])
            # 忽略已知的"字体未嵌入"(docx-js 限制)，只留可处理项
            warns = [w for w in o.get("warnings", []) if "未嵌入字体" not in w]
            issues = fails + warns
            if issues:
                msgs.append(f"  {os.path.basename(p)}: " + "; ".join(issues))
        except Exception:
            pass

    if msgs:
        json.dump({"hookSpecificOutput": {
            "hookEventName": "Stop",
            "additionalContext": (
                "📄 刚生成的 Word 报告 docx_check 发现可处理问题：\n"
                + "\n".join(msgs)
                + "\n（XML/图片引用/markdown 残留等；字体未嵌入是 docx-js 已知限制，已忽略）"
            ),
        }}, sys.stdout)


if __name__ == "__main__":
    main()
