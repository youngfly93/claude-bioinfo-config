#!/usr/bin/env python3
"""SessionStart hook：开会话快速环境预检，结果通过 additionalContext 喂给 Claude，
省得每次手动 /preflight。只读、快速；R 包/字体检查带超时，慢就跳过。"""
import sys
import json
import os
import re
import shutil
import subprocess


def _find_handoff(start):
    """从 cwd 起向上找最多 3 层的 HANDOFF.md（项目根可能是上级目录）。"""
    d = os.path.abspath(start or ".")
    for _ in range(3):
        p = os.path.join(d, "HANDOFF.md")
        if os.path.isfile(p):
            return p
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return None


def _newest_mtime(root, cap=3000):
    """results/scripts/figures 里最新文件的 mtime（有界扫描、跳过垃圾/归档；失败或空返回 0）。
    用于判 HANDOFF 是否过期——过期地图比没图更坑，故让"结果比地图新"这件事在开场可见。"""
    newest = 0.0
    seen = 0
    skip = {".git", ".work", "_archive", "__pycache__", ".bio_harness"}
    for sub in ("results", "scripts", "figures"):
        d = os.path.join(root, sub)
        if not os.path.isdir(d):
            continue
        for r, dirs, files in os.walk(d):
            dirs[:] = [x for x in dirs if x not in skip]
            for f in files:
                if f.startswith("._") or f.startswith("~$"):
                    continue
                seen += 1
                if seen > cap:
                    return newest
                try:
                    mt = os.path.getmtime(os.path.join(r, f))
                    if mt > newest:
                        newest = mt
                except OSError:
                    pass
    return newest


def _commits_since(root, epoch):
    """root 仓库里晚于 epoch(HANDOFF mtime) 的提交数；非 git 仓/失败返回 None。
    比 mtime 更精准地说明"地图落后了多少"——git 是不会漂移的文件真相。"""
    try:
        import datetime
        # +60s 缓冲：忽略"提交 HANDOFF 自己那次"及同刻提交（秒级粒度误报），只算之后真新增的
        iso = datetime.datetime.fromtimestamp(epoch + 60).isoformat()
        r = subprocess.run(["git", "-C", root, "rev-list", "--count",
                            f"--since={iso}", "HEAD"],
                           capture_output=True, text=True, timeout=3)
        if r.returncode == 0 and r.stdout.strip().isdigit():
            return int(r.stdout.strip())
    except Exception:
        pass
    return None


def _find_lock(start):
    """从 cwd 向上找最多 3 层的 .bio_harness/.lock（多 agent 写锁，agent_lock.sh 所写）。"""
    d = os.path.abspath(start or ".")
    for _ in range(3):
        p = os.path.join(d, ".bio_harness", ".lock")
        if os.path.isfile(p):
            return p
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return None


def _lock_note(cwd):
    """浮出多 agent 写锁状态——别的 agent 持锁时提醒本会话先只读，防并发写同一棵树。
    锁是咨询式(无 hook 强制、Codex 也无 hook)，故靠开场'点破'让状态可见、靠自觉遵守。"""
    lp = _find_lock(cwd)
    if not lp:
        return ""
    try:
        import time as _t
        agent, epoch = "?", 0
        with open(lp, encoding="utf-8") as f:
            for line in f:
                if line.startswith("agent="):
                    agent = line[6:].strip()
                elif line.startswith("epoch="):
                    try:
                        epoch = int(line[6:].strip())
                    except ValueError:
                        pass
        ttl = int(os.environ.get("BIO_LOCK_TTL", "1800"))
        age = (int(_t.time()) - epoch) if epoch else ttl + 1
        mins = max(0, age // 60)
        if age >= ttl:
            return (f"\n🔓 写锁陈旧（{agent}，{mins} 分钟前，超 {ttl // 60}min）——"
                    "可 `agent_lock.sh acquire <你> --force` 接管")
        if agent.lower() == "claude":
            return f"\n🔒 你(claude)已持写锁（{mins} 分钟前）——干完记得 release，别把锁留给下一会话"
        return (f"\n⚠ 写锁被 **{agent}** 持有（{mins} 分钟前）——同一棵树本会话先**只读/审计**"
                "（只写 audit/、发现问题只标记不顺手改），别并发写；要写先协调或等其 release")
    except Exception:
        return ""


def main():
    cwd, source = ".", ""
    try:
        data = json.load(sys.stdin)
        if isinstance(data, dict):
            cwd = data.get("cwd") or "."
            source = data.get("source") or ""
    except Exception:
        pass

    # clear/compact 是同一会话内重置上下文：环境没变，跳过(慢的)R 复检，只留交接棒提示
    light = source in ("clear", "compact")
    base = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.path.join(os.path.expanduser("~"), ".claude")  # 插件装别处也能找到
    parts = []

    # 1. 二进制
    for b in ("Rscript", "python3"):
        parts.append(f"{b}{'✓' if shutil.which(b) else '✗缺'}")

    # 2. 关键文件
    files = {
        "house样式": f"{base}/assets/figure-style/nature_theme.R",
        "docx_check": f"{base}/skills/bio-report/scripts/docx_check.py",
        "fig_check": f"{base}/skills/bio-fig-review/scripts/fig_check.py",
    }
    for name, p in files.items():
        parts.append(f"{name}{'✓' if os.path.exists(p) else '✗缺'}")

    # 3. R 包 + CJK 字体（单次 Rscript，带超时；慢就跳过）
    r_status = "同会话跳过" if light else "未检"
    if not light and shutil.which("Rscript"):
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
            m = re.search(r'(?:R包✓|缺包:[^\n]*)(?:\s*·CJK字体[✓✗])?', r.stdout or "")
            r_status = m.group(0).strip() if m else "未检"
        except Exception:
            r_status = "R检查超时(可手动 /preflight)"

    ctx = "🔎 环境预检：" + " · ".join(parts) + " · R: " + r_status

    # 交接棒检测：项目根有 HANDOFF.md → 提示先续上（接手/审批前别凭残留 context 硬接）
    hp = _find_handoff(cwd)
    if hp:
        goal, updated = "", ""
        try:
            with open(hp, encoding="utf-8") as f:
                txt = f.read()
            m = re.search(r'##\s*现在在做什么\s*\n+\s*([^\n]+)', txt)
            if m:
                goal = "：" + m.group(1).strip()[:80]
            dm = re.search(r'\(更新[:：]\s*([^)）]+)[)）]', txt)
            if dm:
                updated = f"（更新 {dm.group(1).strip()}）"
        except Exception:
            pass
        # 新鲜度：优先"HANDOFF 更新后的 git 提交数"(精准、不漂移)，无 git 时回退"结果文件更新"。
        # 告警里直接指向 git——重入先核文件真相，别只信可能过期的手写快照。
        stale = ""
        try:
            root = os.path.dirname(hp)
            hmt = os.path.getmtime(hp)
            n = _commits_since(root, hmt)
            reason = ""
            # 阈值 3：落后 1~2 个提交常是同阶段、不吵；≥3 才是"明显落后"值得核对（防错位）
            if n is not None and n >= 3:
                reason = f"之后已有 {n} 个 git 提交"
            elif n is None and _newest_mtime(root) > hmt + 60:
                reason = "results/scripts 有比它更新的文件"
            if reason:
                stale = (f"\n⚠ HANDOFF 可能过期（{reason}）——续接前先 `git log/status/diff` "
                         "核对文件真相，别照过期地图动手（过期图比没图更坑）")
        except Exception:
            pass
        try:
            rel = os.path.relpath(hp, cwd) if cwd not in (".", None) else hp
        except Exception:
            rel = hp
        ctx += (f"\n📌 检测到交接棒 {rel}{updated}{goal} → 接手/审批前先用 bio-handoff 续上"
                "（读快照 + 复述确认再动手）" + stale)

    # 多 agent 写锁：别的 agent 持锁 → 本会话先只读（防 Claude↔Codex 并发写撞车）
    ctx += _lock_note(cwd)

    json.dump({"hookSpecificOutput": {"hookEventName": "SessionStart",
                                       "additionalContext": ctx}}, sys.stdout)


if __name__ == "__main__":
    main()
