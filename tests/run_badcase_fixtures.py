#!/usr/bin/env python3
"""坏案例 fixture：对 minimal_project 各植入一个缺陷，断言对应的门【必报】。

把 known_issues.md 的高频错从"清单"变成"可执行保证"，并防引擎演进时回归。
- 正向（干净交付应通过）：由 tests/run_harness_smoke.sh 覆盖。
- 负向（坏的必须拦）：本文件覆盖。

每个 case：拷一份干净 fixture → 只植入一个缺陷 → 跑相关 check → 断言
（a）期望的 finding code 出现，且（b）退出码非 0。任一 case 没拦住 → 整体失败。
不改源 fixture（运行时在临时目录变异），所以 fixture 改了也不漂移。
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
H = ROOT / "harness"
FIXTURE = ROOT / "tests" / "fixtures" / "minimal_project"
AI_SCAN = ROOT / "skills" / "bio-deliver" / "scripts" / "ai_trace_scan.py"
ZIP_PACK = ROOT / "skills" / "bio-deliver" / "scripts" / "zip_pack.py"
REQUIRED = ["preflight", "validate_strict", "audit", "ai_scan", "privacy_scan",
            "structure_check", "dedup_check", "package"]


def _cmd(name, ec):
    return {"name": name, "cmd": name, "exit_code": ec, "findings": []}


def _write_proof(proj, commands, artifacts, status="PASS"):
    """直接落一份 proof.json（免跑整条链），供裁判状态机的回归用。"""
    (proj / "delivery").mkdir(exist_ok=True)
    (proj / "audit").mkdir(exist_ok=True)
    (proj / "audit" / "audit.json").write_text("{}", encoding="utf-8")
    proof = {"schema_version": "bio-harness-proof.v1", "status": status,
             "project_root": str(proj), "commands": commands, "artifacts": artifacts,
             "open_warnings": [], "manual_warnings": []}
    (proj / "delivery" / "proof.json").write_text(json.dumps(proof, ensure_ascii=False), encoding="utf-8")


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


def case_privacy_unreadable(proj):
    """隐私门 fail-closed：坏/加密的 Office 文件扫不动，绝不能当'干净'放行 → 必报 P1 SCAN_UNREADABLE。"""
    (proj / "delivery" / "broken.docx").write_bytes(b"not a real docx zip")
    rc, out = run(["python3", H / "delivery" / "privacy_scan.py", proj / "delivery"])
    return ("SCAN_UNREADABLE" in out and rc != 0,
            f"rc={rc} code={'命中' if 'SCAN_UNREADABLE' in out else '缺失'}")


def case_gate_stale_fail(proj):
    """裁判一致性：validate_strict 先 FAIL 后 PASS，strict delivery_gate 必须按【最新】记录放行，
    不能被历史那条 FAIL 永久拦（否则'修好了仍发不出去'）。"""
    cmds = [_cmd("validate_strict", 1)] + [_cmd(n, 0) for n in REQUIRED]  # 首条历史 FAIL + 全 PASS
    _write_proof(proj, cmds, [{"path": "delivery/x_交付.zip"}], status="PASS")
    env = {**os.environ, "PWD": str(proj), "BIO_DELIVERY_GATE_STRICT": "1"}
    r = subprocess.run(["python3", str(ROOT / "hooks" / "delivery_gate.py")],
                       cwd=str(proj), env=env, capture_output=True, text=True)
    return (r.returncode == 0, f"strict gate rc={r.returncode}（期望0=放行修好的交付）")


def case_dedup_required(proj):
    """dedup_check 已进 REQUIRED：proof 少了它（其余齐全）→ finalize PASS 必须被拒。"""
    cmds = [_cmd(n, 0) for n in REQUIRED if n != "dedup_check"]
    _write_proof(proj, cmds, [{"path": "delivery/x_交付.zip"}], status="IN_PROGRESS")
    rc, out = run(["python3", H / "delivery" / "proof.py", "finalize", proj, "--status", "PASS"])
    return (rc != 0 and "dedup_check" in out, f"finalize rc={rc} code={'命中' if 'dedup_check' in out else '缺失'}")


def case_rds_optin(proj):
    """.rds 不再无条件静默丢：默认排除但可 opt-in 保留（合同要的 Seurat/SCE 对象）。"""
    obj = proj / "delivery" / "obj_test"
    obj.mkdir(parents=True, exist_ok=True)
    (obj / "final_seurat.rds").write_bytes(b"x")

    def pack_json():
        # JSON 在 stdout、告警在 stderr——只解析 stdout，别混进 stderr 的 ⚠ 行
        r = subprocess.run(["python3", str(ZIP_PACK), "pack", str(proj / "delivery"), "t"],
                           capture_output=True, text=True)
        return json.loads(r.stdout.strip().splitlines()[-1])

    try:
        o1 = pack_json()
        (proj / "delivery" / ".keep_rds").write_text("", encoding="utf-8")   # opt-in
        o2 = pack_json()
    except Exception as e:                       # noqa: BLE001
        return (False, f"解析 pack 输出失败：{e}")
    default_excluded = bool(o1.get("excluded_rds")) and not o1.get("kept_rds")
    optin_kept = (not o2.get("excluded_rds")) and bool(o2.get("kept_rds"))
    return (default_excluded and optin_kept, f"默认排除={default_excluded} opt-in保留={optin_kept}")


CASES = [
    ("number_mismatch  (P0 数值≠源数据)", case_number_mismatch),
    ("ai_trace         (AI 痕迹残留)",     case_ai_trace),
    ("privacy_leak     (泄漏本机路径)",     case_privacy_leak),
    ("missing_contrast (contrast 缺 denominator)", case_missing_contrast),
    ("privacy_unreadable (坏Office当干净=fail-open)", case_privacy_unreadable),
    ("gate_stale_fail  (修好仍被历史FAIL拦)", case_gate_stale_fail),
    ("dedup_required   (缺 dedup 仍 PASS)", case_dedup_required),
    ("rds_optin        (.rds 静默丢/可保留)", case_rds_optin),
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
