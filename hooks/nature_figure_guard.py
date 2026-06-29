#!/usr/bin/env python3
"""PreToolUse hook：绘图必须走 nature-figure 的 R 后端 + 统一 house 样式。

把"出图一律用 nature-figure 的 R 后端"从 CLAUDE.md 的软约束，补一层机械提醒：
检测到绘图代码时，在动手那一刻注入提醒（只提醒、不阻断，保守、零阻塞）。

- Python 绘图（matplotlib/seaborn/plt./sns./pyplot）→ 提醒：Python 不画图，出图走 R。
- R 绘图（ggplot/ggsave/geom_/ComplexHeatmap/Heatmap/pheatmap）且**未带 house 样式标记**
  （nature_theme.R / theme_nature / save_nature / nature_* …）→ 提醒走 nature-figure + house 样式。
- 已带 house 标记 → 静默（合规，不打扰）。

机制说明：shell hook 无法 100% 验证"是否调用了 nature-figure 技能"，但能在绘图代码出现的瞬间
把绘图政策重新顶到面前——这正是软约束（靠模型自觉）最容易漏的环节。
"""
import sys
import json
import re

PY_PLOT = re.compile(
    r"\bimport\s+matplotlib|\bfrom\s+matplotlib|matplotlib\.|pyplot"
    r"|\bimport\s+seaborn|seaborn\.|\bplt\.|\bsns\.",
    re.IGNORECASE)
R_PLOT = re.compile(
    r"\bggplot\s*\(|\bggsave\s*\(|\bgeom_[a-z]|ComplexHeatmap|\bHeatmap\s*\(|\bpheatmap\s*\(",
    re.IGNORECASE)
HOUSE = re.compile(
    r"nature_theme\.R|theme_nature|save_nature|save_heatmap|nature_volcano|nature_heatmap"
    r"|nature_km|nature_pca|nature_forest|nature_box_sig|nature_enrich|nature_oncoprint|nature_div",
    re.IGNORECASE)

# 只在这些"会写绘图代码"的文件上看 Write/Edit 内容（Bash 看整条命令）
PLOT_FILE_EXT = (".r", ".rmd", ".qmd", ".rnw", ".py", ".ipynb")


def _relevant_text(data):
    tool = data.get("tool_name", "")
    ti = data.get("tool_input", {}) or {}
    if tool == "Bash":
        return ti.get("command", "") or ""
    path = (ti.get("file_path") or ti.get("notebook_path") or "").lower()
    if not path.endswith(PLOT_FILE_EXT):
        return ""
    if tool == "Write":
        return ti.get("content", "") or ""
    if tool == "Edit":
        return ti.get("new_string", "") or ""
    if tool in ("MultiEdit", "NotebookEdit"):
        edits = ti.get("edits") or []
        return "\n".join((e.get("new_string") or "") for e in edits) or ti.get("new_source", "") or ""
    return ""


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    text = _relevant_text(data)
    if not text:
        return

    msg = None
    if PY_PLOT.search(text):
        msg = ("🎨 本机绘图政策：出图/重画一律走 `nature-figure` 的 **R 后端**，"
               "**Python 不画图**（只做数据分析）。请改用 R + house 样式："
               "脚本顶部 `source(\"~/.claude/assets/figure-style/nature_theme.R\")`，"
               "用 `theme_nature` / `save_nature` / `nature_volcano` / `nature_heatmap` 等。")
    elif R_PLOT.search(text) and not HOUSE.search(text):
        msg = ("🎨 本机绘图政策：检测到 R 绘图但未用统一 house 样式。"
               "请走 `nature-figure` 技能的 R 后端——脚本顶部 "
               "`source(\"~/.claude/assets/figure-style/nature_theme.R\")`，"
               "优先用 `theme_nature` / `save_nature` / `nature_volcano` / `nature_heatmap`，"
               "别每图自定义配色/主题（保证一交付一套风格 + CJK 安全）。")

    if msg:
        json.dump({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": msg,
            }
        }, sys.stdout)


if __name__ == "__main__":
    main()
