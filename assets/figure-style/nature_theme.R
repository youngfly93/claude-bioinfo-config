# =====================================================================
# nature_theme.R —— 全局交付 house 样式（CJK 安全版）
# ---------------------------------------------------------------------
# 来源：基于 <project>/<project> 项目验证过的 nature_theme.R 提炼为可复用真源。
# 改动：仅字体层——自动解析 CJK 安全字体，使中英文图都不丢字；
#       配色 / 标度 / 几何 / 导出 / helper 全部保留原设计。
#
# 用法（每个绘图脚本顶部 source 这一份唯一真源）：
#   source("~/.claude/assets/figure-style/nature_theme.R")
#   # 需要指定字体时： options(nature_font = "PingFang SC") 再 source
# =====================================================================

suppressPackageStartupMessages({
  library(ggplot2)
  library(grid)
  library(scales)
})

## CJK 安全字体解析 -------------------------------------------------------
# Latin 观感保持干净；中文永不变方块。source() 时解析一次。
# 优先级：思源/Noto（跨平台）→ 苹方/冬青（macOS）→ 雅黑/黑体（Windows）→ Arial 兜底。
# 注：苹方(PingFang)在 macOS 私有框架路径下，ragg/cairo 都加载不了 → 不入选；
# Hiragino Sans GB 是 macOS 上可访问、双设备都能渲染中文的最稳黑体。
.nature_font_priority <- c(
  "Source Han Sans SC", "Source Han Sans CN", "思源黑体",   # 跨平台首选(若装了)
  "Noto Sans CJK SC", "Noto Sans SC",
  "Hiragino Sans GB", "Heiti SC", "STHeiti",                # macOS 黑体
  "Microsoft YaHei", "SimHei",                              # Windows 黑体
  "Songti SC", "STSong",                                    # 宋体兜底
  "Arial Unicode MS", "WenQuanYi Zen Hei",
  "Arial", "Helvetica"                                      # 纯英文兜底
)

.nature_resolve_font <- function() {
  installed <- tryCatch({
    if (requireNamespace("systemfonts", quietly = TRUE)) {
      sf <- systemfonts::system_fonts()
      # 排除私有框架路径的字体（如苹方），渲染设备加载不了
      sf <- sf[!grepl("PrivateFrameworks", sf$path), , drop = FALSE]
      unique(sf$family)
    } else character(0)
  }, error = function(e) character(0))
  if (length(installed)) {
    hit <- .nature_font_priority[.nature_font_priority %in% installed]
    if (length(hit)) return(hit[[1]])
  }
  "Arial"  # 兜底：保英文；要中文请装一个 CJK 字体或 systemfonts 包
}

# 可用 options(nature_font="苹方-简") 显式覆盖；否则自动解析
NATURE_FONT <- getOption("nature_font", .nature_resolve_font())
if (identical(NATURE_FONT, "Arial")) {
  message("nature_theme: 未检测到 CJK 字体，回退 Arial（中文可能丢字）。",
          "建议装 思源黑体/Noto Sans CJK 或 systemfonts 包。")
} else {
  message("nature_theme: 使用字体 '", NATURE_FONT, "'（CJK 安全）。")
}

## Palette ---------------------------------------------------------------

nature_palette <- c(
  # Hero / proposed method (CEPI / consensus axis)
  hero_dark     = "#0F4D92",
  hero_main     = "#2C5BA6",
  hero_soft     = "#7BA2D3",

  # Positive / improvement
  pos_dark      = "#1F7A4D",
  pos_main      = "#2E9E66",
  pos_soft      = "#9BD3B5",

  # Contrast / baseline
  neg_dark      = "#9B2E25",
  neg_main      = "#C5453C",
  neg_soft      = "#E9A6A1",

  # Accent
  warm          = "#E28E2C",
  teal          = "#33B5A5",
  violet        = "#7E57C2",
  gold          = "#D4A017",

  # Neutrals
  ink           = "#1B1B1B",
  graphite      = "#3F3F3F",
  steel         = "#6E6E6E",
  silver        = "#B5B5B5",
  paper         = "#F2F2F2",
  white         = "#FFFFFF"
)

# Discrete scales for common 2-, 3-, 5-, 6-class plots
nature_pal_3 <- unname(nature_palette[c("hero_main", "neg_main", "warm")])
nature_pal_5 <- unname(nature_palette[c("hero_main", "pos_main", "neg_main", "warm", "violet")])
nature_pal_6 <- c(nature_pal_5, unname(nature_palette["teal"]))

# Sequential / diverging (for heatmaps)
nature_seq    <- c("#FFFFFF", "#E8EEF6", "#B7CBE2", "#7BA2D3", "#3B6BB0", "#0F4D92")
nature_div    <- c("#9B2E25", "#C5453C", "#E9A6A1", "#FFFFFF", "#7BA2D3", "#2C5BA6", "#0F4D92")

## Theme -----------------------------------------------------------------

theme_nature <- function(base_size = 8, base_family = NATURE_FONT, grid = FALSE) {
  th <- theme_classic(base_size = base_size, base_family = base_family) +
    theme(
      axis.line          = element_line(linewidth = 0.35, colour = nature_palette["ink"]),
      axis.ticks         = element_line(linewidth = 0.35, colour = nature_palette["ink"]),
      axis.ticks.length  = unit(2.2, "pt"),
      axis.title         = element_text(size = base_size, colour = nature_palette["ink"]),
      axis.text          = element_text(size = base_size - 0.5, colour = nature_palette["graphite"]),
      strip.background   = element_blank(),
      strip.text         = element_text(size = base_size - 0.3, face = "bold",
                                        colour = nature_palette["ink"]),
      legend.title       = element_text(size = base_size - 0.5,  colour = nature_palette["ink"]),
      legend.text        = element_text(size = base_size - 1.0,  colour = nature_palette["graphite"]),
      legend.key         = element_blank(),
      legend.background  = element_blank(),
      legend.key.height  = unit(8, "pt"),
      legend.key.width   = unit(12, "pt"),
      plot.title         = element_text(size = base_size + 1.0, face = "bold",
                                        colour = nature_palette["ink"], hjust = 0,
                                        margin = margin(b = 4)),
      plot.subtitle      = element_text(size = base_size - 0.5,
                                        colour = nature_palette["steel"], hjust = 0,
                                        margin = margin(b = 6)),
      plot.caption       = element_text(size = base_size - 1.0,
                                        colour = nature_palette["steel"], hjust = 1),
      plot.background    = element_rect(fill = "white", colour = NA),
      panel.background   = element_rect(fill = "white", colour = NA),
      panel.grid         = element_blank(),
      plot.margin        = margin(6, 8, 6, 6)
    )
  if (grid) {
    th <- th + theme(panel.grid.major.y = element_line(linewidth = 0.2,
                                                       colour = nature_palette["paper"]))
  }
  th
}

theme_set(theme_nature())

## Geometry defaults that fit Nature page widths --------------------------
# Single column 89 mm; double column 183 mm; full width 247 mm.
NATURE_W_SINGLE <- 89   # mm
NATURE_W_DOUBLE <- 183
NATURE_W_FULL   <- 247

## Export helper ---------------------------------------------------------
# Saves PNG (preview) + PDF (vector, editable text) at fixed final size.
# Produces TIFF only when tiff=TRUE since it's heavy.
# 字体统一用解析出的 NATURE_FONT，保证 PDF 里中文也嵌得进、可编辑。
save_nature <- function(plot, base_path,
                        width_mm = NATURE_W_DOUBLE,
                        height_mm = 110,
                        dpi = 600,
                        tiff = FALSE,
                        bg = "white",
                        family = NATURE_FONT) {
  w_in <- width_mm  / 25.4
  h_in <- height_mm / 25.4

  # PNG (raster, for fast preview)
  ragg::agg_png(paste0(base_path, ".png"),
                width = w_in, height = h_in,
                units = "in", res = dpi, bg = bg)
  print(plot); dev.off()

  # PDF (vector, editable text)
  grDevices::cairo_pdf(paste0(base_path, ".pdf"),
                       width = w_in, height = h_in, family = family, bg = bg)
  print(plot); dev.off()

  if (isTRUE(tiff)) {
    ragg::agg_tiff(paste0(base_path, ".tiff"),
                   width = w_in, height = h_in,
                   units = "in", res = dpi, bg = bg)
    print(plot); dev.off()
  }
  invisible(base_path)
}

## Forest-plot stats label helper ----------------------------------------
format_hr_label <- function(hr, lo, hi, p, n = NULL, e = NULL) {
  base <- sprintf("HR %.2f (%.2f–%.2f); p = %.2g", hr, lo, hi, p)
  if (!is.null(n) && !is.null(e))
    base <- sprintf("%s; n = %d, events = %d", base, n, e)
  base
}

## Convenience: log10 HR axis with sensible breaks ------------------------
scale_x_hr_log <- function(limits = c(0.5, 4),
                           breaks = c(0.5, 1, 1.5, 2, 3, 4)) {
  scale_x_continuous(trans = "log10", limits = limits,
                     breaks = breaks, labels = breaks,
                     expand = expansion(mult = c(0, 0.02)))
}

## =====================================================================
## Heatmap house style (ComplexHeatmap) —— 全局统一热图风格
## 懒加载：source 本文件不强依赖 ComplexHeatmap，只有调用下列函数时才需要。
## 提炼自 某 T 细胞 z-score 热图，做成可复用、CJK 安全版。
## =====================================================================

# 分组注释 pastel 配色（蓝/橙/紫…，HeatmapAnnotation 取用）
nature_pal_anno <- c("#7FA6C9", "#E0A96D", "#A98DC0", "#8FBF9F", "#C98B8B", "#9B8FC0")

# 标准 z-score 色阶：蓝(#2166AC) → 白 → 红(#B2182B)
nature_heatmap_col <- function(breaks = c(-2, -1, 0, 1, 2),
                               colors = c("#2166AC", "#7FB0D5", "#F7F7F7", "#E89A8C", "#B2182B")) {
  if (!requireNamespace("circlize", quietly = TRUE)) stop("nature_heatmap_col 需要 circlize 包")
  circlize::colorRamp2(breaks, colors)
}

# house 风格 gpar（统一字体 = CJK 安全字体）
nature_hm_gp <- function(size = 6, face = "plain") {
  grid::gpar(fontsize = size, fontfamily = NATURE_FONT, fontface = face)
}

# 顶部分组注释（house 风格）
nature_hm_anno <- function(..., col = NULL) {
  if (!requireNamespace("ComplexHeatmap", quietly = TRUE)) stop("nature_hm_anno 需要 ComplexHeatmap 包")
  ComplexHeatmap::HeatmapAnnotation(
    ...,
    col = col,
    annotation_name_gp = nature_hm_gp(6),
    simple_anno_size   = grid::unit(3, "mm")
  )
}

# 标准热图：套 house 配色/字体/边框/图例；... 透传给 Heatmap() 可覆盖任何项
nature_heatmap <- function(mat, name = "Row Z-score", col = nature_heatmap_col(), ...) {
  if (!requireNamespace("ComplexHeatmap", quietly = TRUE)) stop("nature_heatmap 需要 ComplexHeatmap 包")
  defaults <- list(
    matrix          = mat,
    name            = name,
    col             = col,
    column_title_gp = nature_hm_gp(6.2, "bold"),
    column_names_gp = nature_hm_gp(5.5),
    row_names_gp    = nature_hm_gp(5.5, "italic"),
    heatmap_legend_param = list(
      title_gp      = nature_hm_gp(6.2, "bold"),
      labels_gp     = nature_hm_gp(5.8),
      legend_height = grid::unit(18, "mm"),
      grid_width    = grid::unit(3, "mm"),
      at            = c(-2, -1, 0, 1, 2)
    ),
    border    = TRUE,
    border_gp = grid::gpar(col = "grey40", lwd = 0.4),
    rect_gp   = grid::gpar(col = NA)
  )
  args <- utils::modifyList(defaults, list(...))
  do.call(ComplexHeatmap::Heatmap, args)
}

# 热图导出（draw 进设备；PNG 预览 + PDF 可编辑 + 可选 TIFF；CJK 安全字体）
save_heatmap <- function(ht, base_path, width_mm = 120, height_mm = 180,
                         dpi = 600, tiff = FALSE, family = NATURE_FONT,
                         legend_side = "right") {
  w <- width_mm / 25.4; h <- height_mm / 25.4
  drawit <- function() ComplexHeatmap::draw(ht,
                                            heatmap_legend_side    = legend_side,
                                            annotation_legend_side = legend_side,
                                            merge_legend = TRUE)
  ragg::agg_png(paste0(base_path, ".png"), width = w, height = h, units = "in", res = dpi)
  drawit(); grDevices::dev.off()
  grDevices::cairo_pdf(paste0(base_path, ".pdf"), width = w, height = h, family = family)
  drawit(); grDevices::dev.off()
  if (isTRUE(tiff)) {
    ragg::agg_tiff(paste0(base_path, ".tiff"), width = w, height = h,
                   units = "in", res = dpi, compression = "lzw")
    drawit(); grDevices::dev.off()
  }
  invisible(base_path)
}
