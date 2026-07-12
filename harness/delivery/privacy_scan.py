#!/usr/bin/env python3
"""隐私/泄漏扫描：交付前查 report/delivery 里有没有把本机路径、内网 IP、邮箱等
泄进客户可见文件（外包/客户/患者数据红线）。stdlib only。

- P0：绝对本机路径(/Users/、/home/、C:\\Users\\)、内网私有 IP —— 明确泄漏，必须拦。
- P1：邮箱地址 —— 可能是真人邮箱，复核。
扫文本文件 + docx/pptx/xlsx 正文 xml。退出码：有 P0/P1 → 1，干净 → 0。
注：不自动改（交付物得人工确认改哪），只报告。
"""
import os, sys, re, json, zipfile

PATTERNS = [
    ("P0", "ABS_USER_PATH", re.compile(r"(?:/Users/|/home/)[^/\s\"'<>]+|[A-Za-z]:\\Users\\[^\\\s\"'<>]+")),
    ("P0", "INTERNAL_IP", re.compile(r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b")),
    ("P1", "EMAIL", re.compile(r"[A-Za-z0-9.+_-]+@[A-Za-z0-9-]+\.[A-Za-z0-9.-]+")),
]
TEXT_EXTS = (".md", ".txt", ".csv", ".tsv", ".html", ".r", ".rmd", ".py", ".sh", ".json", ".yaml", ".yml")
OFFICE_EXTS = (".docx", ".pptx", ".xlsx")
SKIP_DIRS = {".git", ".bio_harness", "audit", "_archive", ".work"}
SKIP_NAMES = {"proof.json", "goal_proof.md"}  # 内部 QA，不算客户可见


def _scan_text(text, path, out):
    for sev, code, pat in PATTERNS:
        for m in pat.finditer(text):
            out.append({"file": path, "severity": sev, "code": code,
                        "match": m.group()[:80], "pos": m.start()})


def scan(directory):
    out = []
    for root, dns, fns in os.walk(directory):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        for f in fns:
            if f in SKIP_NAMES:
                continue
            p = os.path.join(root, f)
            ext = os.path.splitext(f)[1].lower()
            if ext not in TEXT_EXTS and ext not in OFFICE_EXTS:
                continue
            try:
                if ext in TEXT_EXTS:
                    _scan_text(open(p, encoding="utf-8", errors="ignore").read(), p, out)
                elif ext in OFFICE_EXTS:
                    with zipfile.ZipFile(p) as z:
                        for n in z.namelist():
                            if n.endswith(".xml"):
                                _scan_text(z.read(n).decode("utf-8", "ignore"), p, out)
            except Exception as e:
                # fail-closed：本该扫的文件扫不动（损坏/加密/异常格式）绝不当"干净"放行——
                # 无法检查 ≠ 检查通过。升 P1，逼人工确认里面没泄漏。
                out.append({"file": p, "severity": "P1", "code": "SCAN_UNREADABLE",
                            "match": str(e)[:80], "pos": 0})
    return out


def main():
    target = sys.argv[2] if len(sys.argv) > 2 else (sys.argv[1] if len(sys.argv) > 1 else "delivery")
    findings = scan(target)
    print(json.dumps(findings, ensure_ascii=False, indent=2))
    bad = [x for x in findings if x["severity"] in ("P0", "P1")]
    if bad:
        n0 = sum(x["severity"] == "P0" for x in bad)
        print(f"privacy_scan: 发现 {len(bad)} 处泄漏风险（P0={n0}）—— 交付前必须处理。", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
