#!/usr/bin/env python3
"""PreCompact hook：压缩(manual/auto)时给压缩后的模型注入交接提醒。

shell 钩子无法替模型撰写有思考的交接，也保证不了"压缩前先写好文件"——压缩照常发生。
它能做的、也最有价值的：在压缩边界注入一条提醒，让压缩后的(新)模型立刻处理交接棒：
  ① 有 HANDOFF.md → 先读它续接，审核口径以它/plan.md 为准，别凭压缩摘要硬接；
  ② 无但像生信项目(有 plan.md) → 提醒用 bio-handoff 补写交接棒；
  ③ 都没有 → 静默(不在非生信会话里制造噪音)。
覆盖 auto-compact——这是自定义命令包装够不着的盲区。
"""
import sys
import json
import os


def _find_up(start, name, levels=3):
    d = os.path.abspath(start or ".")
    for _ in range(levels):
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return None


def main():
    cwd, trigger = ".", "?"
    try:
        data = json.load(sys.stdin)
        if isinstance(data, dict):
            cwd = data.get("cwd") or "."
            trigger = data.get("trigger") or "?"
    except Exception:
        pass

    tlabel = {"manual": "手动 /compact", "auto": "自动压缩"}.get(trigger, "上下文压缩")
    handoff = _find_up(cwd, "HANDOFF.md")
    plan = _find_up(cwd, "plan.md")

    msg = None
    if handoff:
        try:
            rel = os.path.relpath(handoff, cwd) if cwd not in (".", None) else handoff
        except Exception:
            rel = handoff
        msg = (f"🔄 刚发生{tlabel}。项目根有交接棒 {rel} → 继续/审批前**先读它并复述确认**，"
               "审核口径以 HANDOFF.md / plan.md 为准，别凭压缩摘要硬接。")
    elif plan:
        msg = (f"🔄 刚发生{tlabel}，未见 HANDOFF.md。若继续生信分析/审批，"
               "**先用 bio-handoff 补写交接棒**（锁下一步 + 审核口径合同）再往下走，防断层/口径漂移。")

    if msg:
        json.dump({"hookSpecificOutput": {"hookEventName": "PreCompact",
                                          "additionalContext": msg}}, sys.stdout)


if __name__ == "__main__":
    main()
