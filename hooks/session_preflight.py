#!/usr/bin/env python3
"""SessionStart hook：开会话快速环境预检，结果通过 additionalContext 喂给 Claude，
省得每次手动 /preflight。只读、快速；R 包/字体检查带超时，慢就跳过。"""
import sys
import json
import os
import shutil
import subprocess


def main():
    try:
        json.load(sys.stdin)
    except Exception:
        pass

    home = os.path.expanduser("~")
    parts = []

    # 1. 二进制
    for b in ("Rscript", "python3"):
        parts.append(f"{b}{'✓' if shutil.which(b) else '✗缺'}")

    # 2. 关键文件
    files = {
        "house样式": f"{home}/.claude/assets/figure-style/nature_theme.R",
        "docx_check": f"{home}/.claude/skills/bio-report/scripts/docx_check.py",
        "fig_check": f"{home}/.claude/skills/bio-fig-review/scripts/fig_check.py",
    }
    for name, p in files.items():
        parts.append(f"{name}{'✓' if os.path.exists(p) else '✗缺'}")

    # 3. R 包 + CJK 字体（单次 Rscript，带超时；慢就跳过）
    r_status = "未检"
    if shutil.which("Rscript"):
        try:
            r = subprocess.run(
                ["Rscript", "-e",
                 'pk<-c("ggplot2","ComplexHeatmap","ragg","systemfonts");'
                 'miss<-pk[!sapply(pk,requireNamespace,quietly=TRUE)];'
                 'f<-tryCatch(systemfonts::system_fonts(),error=function(e)NULL);'
                 'cjk<-!is.null(f)&&any(grepl("Hiragino|Noto.*CJK|Source Han|PingFang|SimHei|YaHei",f$family));'
                 'cat(if(length(miss))paste0("缺包:",paste(miss,collapse=",")) else "R包✓",'
                 'if(cjk)"·CJK字体✓" else "·CJK字体✗")'],
                capture_output=True, text=True, timeout=6)
            import re
            m = re.search(r'(?:R包✓|缺包:[^\n]*)(?:\s*·CJK字体[✓✗])?', r.stdout or "")
            r_status = m.group(0).strip() if m else "未检"
        except Exception:
            r_status = "R检查超时(可手动 /preflight)"

    ctx = "🔎 环境预检：" + " · ".join(parts) + " · R: " + r_status
    json.dump({"hookSpecificOutput": {"hookEventName": "SessionStart",
                                       "additionalContext": ctx}}, sys.stdout)


if __name__ == "__main__":
    main()
