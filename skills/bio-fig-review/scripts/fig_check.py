#!/usr/bin/env python3
"""
bio-fig-review 确定性图表技术检查。

只查**机器能可靠判定**的客观项：分辨率/像素尺寸、白底比例、透明通道、
矢量 vs 位图。网格线/配色/可读性这类主观项不在这里硬判（易误报），留给肉眼审查。

用法:
    python3 fig_check.py check <文件或目录> [--dpi 300] [--white 0.90]
    # → JSON；退出码 0=全部 OK，1=有 flag
"""
import sys
import os
import json

EXTS = (".png", ".jpg", ".jpeg", ".tiff", ".tif", ".pdf", ".svg")


def _gather(target):
    if os.path.isfile(target):
        return [target]
    out = []
    for root, _, files in os.walk(target):
        for f in files:
            if f.lower().endswith(EXTS):
                out.append(os.path.join(root, f))
    return sorted(out)


def _check_raster(path, dpi_target, white_target):
    try:
        from PIL import Image
    except ImportError:
        return {"type": "raster", "skipped": "未安装 Pillow(PIL)，未检查"}
    r = {"type": "raster", "flags": []}
    with Image.open(path) as im:
        r["size_px"] = list(im.size)
        r["mode"] = im.mode
        dpi = im.info.get("dpi")
        # PIL 常把 300 存成 299.9994，比较前先四舍五入，避免假阳性
        dmin = round(min(dpi)) if dpi else None
        r["dpi"] = [round(x) for x in dpi] if dpi else None
        has_alpha = im.mode in ("RGBA", "LA") or "transparency" in im.info
        r["alpha"] = has_alpha

        # DPI 判定（仅当图片自带 DPI 信息时）
        if dmin is not None and dmin < dpi_target:
            r["flags"].append(f"低分辨率 {dmin}DPI < {dpi_target}")
        elif dmin is None:
            r["flags"].append("无 DPI 信息（请按像素尺寸/用途人工确认）")

        # 白底比例：采样四条边的像素，看近白(>=245)占比
        rgb = im.convert("RGB")
        w, h = rgb.size
        step = max(1, w // 200, h // 200)
        px = rgb.load()
        border, white = 0, 0
        for x in range(0, w, step):
            for y in (0, h - 1):
                c = px[x, y]; border += 1
                if c[0] >= 245 and c[1] >= 245 and c[2] >= 245:
                    white += 1
        for y in range(0, h, step):
            for x in (0, w - 1):
                c = px[x, y]; border += 1
                if c[0] >= 245 and c[1] >= 245 and c[2] >= 245:
                    white += 1
        ratio = white / border if border else 0
        r["border_white_ratio"] = round(ratio, 3)
        if has_alpha:
            r["flags"].append("含透明通道（交付通常要纯白底，建议拼合为白底）")
        elif ratio < white_target:
            r["flags"].append(f"边缘白底比例 {ratio:.0%} < {white_target:.0%}（可能非纯白底，请人工确认）")
    return r


def _check_svg(path):
    r = {"type": "svg(矢量)", "flags": []}
    data = open(path, "rb").read()
    if b"<image" in data or b"base64" in data:
        r["flags"].append("SVG 内嵌位图（image/base64），并非真矢量，放大会糊")
    return r


def _check_pdf(path):
    """轻量启发式：有 /Image 无 /Font 多半是扫描/内嵌位图。"""
    r = {"type": "pdf", "flags": [], "heuristic": True}
    data = open(path, "rb").read()
    has_img = b"/Image" in data or b"/DCTDecode" in data
    has_font = b"/Font" in data
    r["has_image"], r["has_font"] = has_img, has_font
    if has_img and not has_font:
        r["flags"].append("疑似内嵌位图/扫描的 PDF（有图像无文本字体），非矢量")
    return r


def check(target, dpi_target=300, white_target=0.90):
    results = []
    for p in _gather(target):
        ext = os.path.splitext(p)[1].lower()
        try:
            if ext == ".svg":
                item = _check_svg(p)
            elif ext == ".pdf":
                item = _check_pdf(p)
            else:
                item = _check_raster(p, dpi_target, white_target)
        except Exception as e:
            item = {"type": "error", "flags": [f"读取失败: {e}"]}
        item["file"] = p
        results.append(item)
    any_flag = any(it.get("flags") for it in results)
    return {"checked": len(results), "with_flags": sum(1 for it in results if it.get("flags")),
            "results": results, "pass": not any_flag}


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) >= 2 and args[0] == "check":
        target = args[1]
        dpi_t, white_t = 300, 0.90
        if "--dpi" in args:
            dpi_t = int(args[args.index("--dpi") + 1])
        if "--white" in args:
            white_t = float(args[args.index("--white") + 1])
        out = check(target, dpi_t, white_t)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        sys.exit(0 if out["pass"] else 1)
    else:
        print("Usage: fig_check.py check <文件或目录> [--dpi 300] [--white 0.90]")
        sys.exit(2)
