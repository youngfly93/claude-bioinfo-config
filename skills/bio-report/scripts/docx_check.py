#!/usr/bin/env python3
"""
bio-report 交付 Word 报告确定性校验。

只读、保守：报告问题，绝不自动改/删。Markdown 残留扫描的是**可见文字**
（w:t 节点）而非裸 XML，避免把 XML 属性误判成残留（历史上正则误报的根源）。

用法:
    python3 docx_check.py check <report.docx>
    # → JSON；退出码 0=全部通过，1=有 WARN/FAIL
"""
import sys
import os
import re
import json
import zipfile
import xml.etree.ElementTree as ET

W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# 可见文字里的 Markdown 残留特征（保守，低误报）
MD_PATTERNS = [
    (r"\*\*[^\s*][^*]*\*\*", "粗体 **xx**"),
    (r"(?:^|\s)#{1,6}\s+\S", "标题 # xx"),
    (r"`[^`]+`", "代码 `xx`"),
    (r"-\s*\[[ xX]\]", "任务框 - [ ]"),
    (r"\|[^|\n]+\|[^|\n]+\|", "表格管道 |a|b|"),
]


def _texts(zf, part):
    """提取某个 part 里所有 w:t 可见文字，按段聚合返回 list[str]。"""
    try:
        root = ET.fromstring(zf.read(part))
    except Exception:
        return []
    out = []
    for para in root.iter(f"{W_NS}p"):
        seg = "".join(t.text or "" for t in para.iter(f"{W_NS}t"))
        if seg.strip():
            out.append(seg)
    return out


def check(path):
    res = {"file": os.path.basename(path), "xml_ok": True,
           "image": {}, "fonts": {}, "markdown_residue": [], "warnings": [], "fail": []}
    if not os.path.exists(path):
        res["fail"].append(f"文件不存在: {path}")
        res["xml_ok"] = False
        return res

    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()

        # 1. XML 完整性：逐个解析所有 .xml
        for n in names:
            if n.endswith(".xml"):
                try:
                    ET.fromstring(zf.read(n))
                except Exception as e:
                    res["xml_ok"] = False
                    res["fail"].append(f"XML 解析失败 {n}: {e}")

        # 2. 图片引用对账：word/media 实际图片 vs document.xml 引用数
        # 排除目录条目（docx-js 会写显式的 "word/media/" 目录条目，python-docx 不会）
        media = [n for n in names if n.startswith("word/media/") and not n.endswith("/")]
        doc_xml = zf.read("word/document.xml").decode("utf-8", "ignore") if "word/document.xml" in names else ""
        ref_ids = set(re.findall(r'r:embed="([^"]+)"', doc_xml))
        res["image"] = {"media_files": len(media), "doc_refs": len(ref_ids),
                        "match": len(media) == len(ref_ids)}
        if len(media) != len(ref_ids):
            res["warnings"].append(
                f"图片数不一致：media/ {len(media)} 张 vs 文档引用 {len(ref_ids)} 处（可能有未引用或断链图片）")

        # 3. 字体：声明的字体 + 是否嵌入
        declared = set()
        if "word/fontTable.xml" in names:
            ft = zf.read("word/fontTable.xml").decode("utf-8", "ignore")
            declared = set(re.findall(r'w:name="([^"]+)"', ft))
        embedded = [n for n in names if n.startswith("word/fonts/")]
        # 可见文字里是否含 CJK
        all_text = "".join("".join(_texts(zf, "word/document.xml")))
        has_cjk = bool(re.search(r"[一-鿿]", all_text))
        res["fonts"] = {"declared": sorted(declared), "embedded_count": len(embedded),
                        "has_cjk_text": has_cjk}
        if has_cjk and not embedded:
            res["warnings"].append(
                "含中文但未嵌入字体：客户端若无宋体/黑体会被替换。建议开启 embedTrueTypeFonts 嵌入字体。")

        # 4. Markdown 残留（扫可见文字，保守）
        for seg in _texts(zf, "word/document.xml"):
            for pat, label in MD_PATTERNS:
                m = re.search(pat, seg)
                if m:
                    ctx = seg.strip()
                    res["markdown_residue"].append(
                        {"type": label, "context": ctx[:60] + ("…" if len(ctx) > 60 else "")})
                    break
        if res["markdown_residue"]:
            res["warnings"].append(f"疑似 Markdown 残留 {len(res['markdown_residue'])} 处（只标不删，请人工确认）")

    res["pass"] = res["xml_ok"] and not res["fail"] and not res["warnings"]
    return res


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "check":
        r = check(sys.argv[2])
        print(json.dumps(r, ensure_ascii=False, indent=2))
        sys.exit(0 if r.get("pass") else 1)
    else:
        print("Usage: docx_check.py check <report.docx>")
        sys.exit(2)
