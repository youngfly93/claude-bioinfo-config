---
name: bio-fig-review
description: >-
  批量审查生信项目图表是否符合 SCI/交付标准。用于检查 figures/results/output/plots 中的 PNG/JPG/TIFF/PDF/SVG
  的分辨率、白底、网格线、标签、图例、配色、统计标注、样本数和图表-数据一致性。
  触发条件：用户说"审图"、"图表审查"、"fig-review"、"检查图片"、"SCI 图表标准"、"这些图能交付吗"。
  完整交付、打包、发客户请优先使用 bio-deliver；本 skill 只负责图表专项审查。
  不适用于：从头生成或重画论文图（用 nature-figure 的 R 版本）、调试生成图的代码错误（用 bio-diagnose）。
---

# 生信图表审查

批量检查项目中的图表质量。默认只读：先审查并报告问题，不自动重画。

> 完整交付场景优先用 `bio-deliver`。本 skill 是图表专项审查，可被 `bio-deliver` 编排，也可在只需要审图时单独使用。

## 扫描范围

查找常见图表目录：

```bash
find . -type f \( -iname "*.png" -o -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.tiff" -o -iname "*.tif" -o -iname "*.pdf" -o -iname "*.svg" \) \
  | grep -iE "(figure|figures|result|results|output|plot|plots|fig)" \
  | sort
```

如果候选文件很多，先按 `plan.md`、报告引用和最近修改时间确定优先审查集合。

## 审查维度

1. **基本规范**
   - 背景是否纯白或符合期刊/图像类型要求。
   - 是否有多余网格线、边框、低清截图痕迹。
   - 位图分辨率是否满足交付要求，通常目标 `>=300 DPI` 或足够像素尺寸。

2. **可读性**
   - 字体大小、坐标轴、标签、图例缩放后是否可读。
   - 配色是否协调、可区分，避免不可读的红绿对比。
   - 热图/火山图/UMAP/箱线图是否有必要色标和注释。

3. **统计与标注**
   - 显著性标注（`*`, `**`, `***`, `ns`）是否有统计依据。
   - 样本数、组别名称、坐标轴单位是否与实验设计一致。
   - 图题、编号、panel label 是否准确连续。

4. **数据一致性**
   - 图中数值是否能追溯到结果表或脚本。
   - 如果图由 R/Python 生成，同时检查绘图脚本中的输入、过滤、阈值和保存参数。

5. **风格统一（house 样式）**
   - 同一交付内所有图是否共用一套配色/字体/尺寸（一个交付一套风格），还是每张各画各的。
   - 生成脚本是否 source 了 house 真源 `~/.claude/assets/figure-style/nature_theme.R`，并用其中的
     `theme_nature` + `nature_volcano/km/enrich_dot/pca/box_sig/forest/oncoprint/heatmap` 等模块
     （这些模块内置 Nature 配色、阈值线/显著性标注、CJK 安全字体）。
   - 风格不一致 / 各自为政 → 建议统一 source 这份重画，而非逐张手调。

## 技术检查

**客观项先跑确定性脚本**（分辨率/像素尺寸/白底比例/透明/矢量），不靠肉眼估：

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/fig_check.py check <figures目录或单图> [--dpi 300] [--white 0.90]
# 若无 ${CLAUDE_SKILL_DIR}：~/.claude/skills/bio-fig-review/scripts/fig_check.py
# 每张图输出 DPI/像素/白底比例/透明/矢量判定 + flags；退出码 0=全通过
```

- 脚本 flag 的项逐张核对。
- **主观项**（网格线、配色、可读性、统计标注、数据一致性）脚本不判，仍用 `view_image` 视觉检查 + 追溯结果表/脚本。
- PDF/SVG 脚本给"矢量 vs 内嵌位图"的启发式判断，必要时再人工确认文本是否可编辑。

## 输出格式

```markdown
## 图表审查报告

| # | 文件 | 尺寸/DPI | 白底 | 无多余网格 | 标签/图例 | 配色 | 数据一致性 | 总评 |
|---|------|----------|------|------------|-----------|------|------------|------|

## 需要修改的图表

### [文件路径]
- 问题：[具体问题]
- 依据：[视觉检查/技术参数/脚本/结果表]
- 建议：[如何重画或修正]
```

## 纪律

- 先报告，不擅自覆盖原图。
- 不用“好看/不好看”替代具体证据。
- 若用户要求修图/重画，统一用 `nature-figure` 的 **R 后端**（ggplot2 / ComplexHeatmap），并在脚本顶部
  `source("~/.claude/assets/figure-style/nature_theme.R")`、优先调 `nature_*` 模块 + `save_nature()` 导出，
  保证全交付一套风格、CJK 安全；优先改生成脚本而不是手工处理输出图；不用 Python 画图。
