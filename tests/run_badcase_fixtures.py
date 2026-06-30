#!/usr/bin/env python3
"""坏案例 fixture：对 minimal_project 各植入一个缺陷，断言对应的门【必报】。

把 known_issues.md 的高频错从"清单"变成"可执行保证"，并防引擎演进时回归。
- 正向（干净交付应通过）：由 tests/run_harness_smoke.sh 覆盖。
- 负向（坏的必须拦）：本文件覆盖。

每个 case：拷一份干净 fixture → 只植入一个缺陷 → 跑相关 check → 断言
（a）期望的 finding code 出现，且（b）退出码非 0。任一 case 没拦住 → 整体失败。
不改源 fixture（运行时在临时目录变异），所以 fixture 改了也不漂移。
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
H = ROOT / "harness"
FIXTURE = ROOT / "tests" / "fixtures" / "minimal_project"
AI_SCAN = ROOT / "skills" / "bio-deliver" / "scripts" / "ai_trace_scan.py"


def fresh():
    """拷一份干净 fixture 到临时目录，返回 (tmp_root, project_dir)。"""
    tmp = Path(tempfile.mkdtemp(prefix="badcase_"))
    proj = tmp / "p"
    shutil.copytree(FIXTURE, proj)
    return tmp, proj


def run(args):
    r = subprocess.run([str(a) for a in args], capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr)


def edit(path, fn):
    path.write_text(fn(path.read_text(encoding="utf-8")), encoding="utf-8")


# 每个 case 返回 (ok, detail)；ok=True 表示门确实拦住了植入的缺陷。

def case_number_mismatch(proj):
    """known_issues #1（P0）：报告承重数字与源表不一致。"""
    edit(proj / "report_claims.tsv", lambda t: t.replace("\t42\t", "\t999\t"))
    rc, out = run(["python3", H / "quality" / "report_claims_check.py", proj, "--strict"])
    return ("REPORT_CLAIM_VALUE_NOT_IN_SOURCE" in out and rc != 0,
            f"rc={rc} code={'命中' if 'REPORT_CLAIM_VALUE_NOT_IN_SOURCE' in out else '缺失'}")


def case_ai_trace(proj):
    """known_issues #10：AI 痕迹残留在交付文件中。"""
    edit(proj / "delivery" / "final_report.md",
         lambda t: t + "\n\n作为一个AI语言模型，我建议进一步分析。\n")
    rc, out = run(["python3", AI_SCAN, "scan", proj / "delivery"])
    return (rc != 0 and "作为" in out, f"rc={rc} 命中AI痕迹={'是' if '作为' in out else '否'}")


def case_privacy_leak(proj):
    """客户数据红线：交付文件泄漏本机绝对路径。"""
    edit(proj / "delivery" / "final_report.md",
         lambda t: t + "\n\n数据位于 /Users/realname/Desktop/secret.xlsx\n")
    rc, out = run(["python3", H / "delivery" / "privacy_scan.py", proj / "delivery"])
    return ("ABS_USER_PATH" in out and rc != 0,
            f"rc={rc} code={'命中' if 'ABS_USER_PATH' in out else '缺失'}")


def case_missing_contrast(proj):
    """known_issues #4 相关：contrast 设计不完整（缺 denominator）。"""
    edit(proj / "contract.yaml",
         lambda t: "\n".join(l for l in t.splitlines() if "denominator:" not in l) + "\n")
    rc, out = run(["python3", H / "quality" / "contrast_lint.py", proj, "--strict"])
    return ("CONTRAST_DENOMINATOR_MISSING" in out and rc != 0,
            f"rc={rc} code={'命中' if 'CONTRAST_DENOMINATOR_MISSING' in out else '缺失'}")


CASES = [
    ("number_mismatch  (P0 数值≠源数据)", case_number_mismatch),
    ("ai_trace         (AI 痕迹残留)",     case_ai_trace),
    ("privacy_leak     (泄漏本机路径)",     case_privacy_leak),
    ("missing_contrast (contrast 缺 denominator)", case_missing_contrast),
]


def main():
    if not FIXTURE.is_dir():
        print(f"找不到 fixture：{FIXTURE}")
        return 1
    fails = 0
    print("== 坏案例 fixture（门必须拦住每个植入的缺陷）==")
    for name, fn in CASES:
        tmp, proj = fresh()
        try:
            ok, detail = fn(proj)
        except Exception as e:               # noqa: BLE001
            ok, detail = False, f"异常：{e}"
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        print(f"  [{'拦住' if ok else '漏过'}] {name}  ({detail})")
        if not ok:
            fails += 1
    if fails:
        print(f"badcase fixtures: FAIL（{fails} 个缺陷没被拦住）")
        return 1
    print(f"badcase fixtures: PASS（{len(CASES)} 个缺陷全部拦住）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
