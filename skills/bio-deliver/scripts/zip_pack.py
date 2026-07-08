#!/usr/bin/env python3
"""Windows 兼容 ZIP 打包工具。确保中文文件名不乱码。"""

import zipfile
import os
import sys
import datetime
import hashlib
import fnmatch

# 精确名（目录或文件）——绝不进客户包。对齐 SKILL.md「过程记录不进交付包」，
# 从"嘴上说"升级为机械强制：无论收集的 agent 是否手工挑干净，这些都进不了 ZIP。
EXCLUDE = {
    # 系统/VCS/R 运行态
    '.DS_Store', '__MACOSX', '.git', '.Rhistory', '.RData', 'Thumbs.db', '__pycache__',
    # harness QA 内部产物（proof 含 harness 路径，绝不发客户）
    '.bio_harness', 'proof.json', 'goal_proof.md',
    # 过程记录 / 审计 / 内部台账 / 草稿区（内部真源，不发客户）
    'audit', '.work', '_archive',
    'HANDOFF.md', 'DOCS_INDEX.md', 'execution_log.md', 'fix_log.md',
    'delivery_manifest.tsv', 'delivery_md5.txt',
}
# 按 basename 模式拦的中间/日志/系统垃圾（fnmatch）——含 macOS AppleDouble `._*` 与 Excel 锁 `~$*`
EXCLUDE_PATTERNS = ('*.log', '*.rds', '*.RData', '*.pyc', '*.tmp', '._*', '~$*')

def should_exclude(path: str) -> bool:
    parts = path.split(os.sep)
    if any(p in EXCLUDE for p in parts):
        return True
    base = parts[-1]
    return any(fnmatch.fnmatch(base, pat) for pat in EXCLUDE_PATTERNS)

def pack(delivery_dir: str, project_name: str = "项目"):
    """打包为 Windows 兼容 ZIP；解压即得**单一干净根目录**（项目名_交付_DATE/，不带 delivery 外壳）。
    返回 (zip_path, excluded)：excluded 为被机械排除的过程/中间文件相对路径列表（透明、不静默丢）。"""
    delivery_dir = os.path.abspath(delivery_dir)
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    zip_name = f"{project_name}_交付_{date_str}.zip"
    zip_path = os.path.join(os.path.dirname(delivery_dir), zip_name)

    # 单一干净根目录：delivery 内只有一个子目录(现成的项目交付夹)→ 用它当根；
    # 否则把 delivery 里的内容收进一个 {项目名_交付_DATE}/ 根，避免客户解压出 "delivery/" 通用壳或散文件。
    entries = [e for e in os.listdir(delivery_dir)
               if e not in EXCLUDE and not e.startswith('.')]
    subdirs = [e for e in entries if os.path.isdir(os.path.join(delivery_dir, e))]
    loose = [e for e in entries if os.path.isfile(os.path.join(delivery_dir, e))]
    if len(subdirs) == 1 and not loose:
        src, root_name = os.path.join(delivery_dir, subdirs[0]), subdirs[0]
    else:
        src, root_name = delivery_dir, zip_name[:-4]  # 合成根 = 项目名_交付_DATE

    excluded = []
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        for root, dirs, files in os.walk(src):
            dirs[:] = [d for d in dirs if d not in EXCLUDE]
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, src)
                arcname = os.path.join(root_name, rel)
                if should_exclude(arcname):
                    excluded.append(rel)
                    continue
                zf.write(full, arcname)

    return zip_path, sorted(excluded)

def verify(zip_path: str) -> dict:
    """验证 ZIP 完整性，返回结果字典。"""
    with zipfile.ZipFile(zip_path, 'r') as zf:
        bad = zf.testzip()
        names = zf.namelist()
        total_size = sum(i.file_size for i in zf.infolist())
    return {
        "crc_ok": bad is None,
        "bad_file": bad,
        "file_count": len(names),
        "total_size_mb": round(total_size / 1024 / 1024, 1),
        "files": names
    }

def checksum(delivery_dir: str) -> str:
    """生成 delivery/ 的 MD5 校验和文件，返回文件路径。"""
    out_path = os.path.join(os.path.dirname(delivery_dir), "delivery_md5.txt")
    lines = []
    for root, dirs, files in sorted(os.walk(delivery_dir)):
        dirs.sort()
        for f in sorted(files):
            full = os.path.join(root, f)
            rel = os.path.relpath(full, delivery_dir)
            md5 = hashlib.md5(open(full, 'rb').read()).hexdigest()
            lines.append(f"{md5}  {rel}")
    with open(out_path, 'w') as fh:
        fh.write('\n'.join(lines) + '\n')
    return out_path

if __name__ == "__main__":
    import json
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "pack":
        path, excluded = pack(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "项目")
        print(json.dumps({"zip_path": path,
                          "excluded_count": len(excluded),
                          "excluded": excluded}, ensure_ascii=False))
    elif cmd == "verify":
        result = verify(sys.argv[2])
        print(json.dumps(result, ensure_ascii=False))
    elif cmd == "checksum":
        path = checksum(sys.argv[2])
        print(json.dumps({"checksum_path": path}))
    else:
        print("Usage: zip_pack.py [pack|verify|checksum] <path> [project_name]")
