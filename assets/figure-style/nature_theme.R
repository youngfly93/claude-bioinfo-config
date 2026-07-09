# =====================================================================
# nature_theme.R —— 全局交付 house 样式（CJK 安全版）
# ---------------------------------------------------------------------
# 来源：基于真实交付项目验证过的 nature_theme.R 提炼为可复用真源。
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
## 提炼自某交付项目的 T 细胞 z-score 热图，做成可复用、CJK 安全版。
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
# 注意：annotation_legend_param 必须显式带 CJK 字体，否则注释图例的中文标签会变豆腐块
nature_hm_anno <- function(..., col = NULL) {
  if (!requireNamespace("ComplexHeatmap", quietly = TRUE)) stop("nature_hm_anno 需要 ComplexHeatmap 包")
  ComplexHeatmap::HeatmapAnnotation(
    ...,
    col = col,
    annotation_name_gp = nature_hm_gp(6),
    annotation_legend_param = list(
      title_gp  = nature_hm_gp(6.2, "bold"),
      labels_gp = nature_hm_gp(5.8)
    ),
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

## =====================================================================
## ggplot 生信图模块 —— 全局统一「火山图 / KM 生存 / 富集 dotplot」
## 蓝本：从多个已验收的 Nature 级交付图反推，收口成可复用函数。
## 三者都继承 theme_nature() → 自动 CJK 安全；配色统一 Nature 套。
## 懒依赖：volcano 标注需 ggrepel；KM 需 survival(+patchwork 出风险表)。
## =====================================================================

# 方向语义色：上调/高危/肿瘤=红，下调/低危/正常=蓝，ns=灰（与热图 RdBu 同族）
nature_sig_col <- c(Up = "#D24B40", Down = "#3775BA", ns = "#D8D8D8",
                    High = "#D24B40", Low = "#3775BA",
                    Tumor = "#D24B40", Normal = "#3775BA")

## ---- 火山图 nature_volcano() ----------------------------------------
# df 至少含 logFC 列与校正 p 列；label 给基因名列则标注 top_n 上/下调基因。
# 内置阈值虚线、Up/Down 计数图例、ggrepel 标注（蓝本：fig1b_deg.R）。
nature_volcano <- function(df, lfc = "logFC", p = "adj.P.Val", label = NULL,
                           fc_thresh = 1, p_thresh = 0.05, top_n = 10,
                           title = NULL, subtitle = NULL,
                           xlab = expression(log[2]~fold-change),
                           ylab = expression(-log[10]~adjusted~italic(P)),
                           cap_p = 1e-300) {
  df <- as.data.frame(df)
  stopifnot(all(c(lfc, p) %in% colnames(df)))
  x <- as.numeric(df[[lfc]]); pv <- as.numeric(df[[p]])
  sig <- ifelse(pv < p_thresh & x >=  fc_thresh, "Up",
         ifelse(pv < p_thresh & x <= -fc_thresh, "Down", "ns"))
  v <- data.frame(x = x, y = -log10(pmax(pv, cap_p)),
                  sig = factor(sig, levels = c("Up", "Down", "ns")))
  if (!is.null(label) && label %in% colnames(df)) v$lab <- as.character(df[[label]])
  n_up <- sum(v$sig == "Up"); n_dn <- sum(v$sig == "Down")

  p_out <- ggplot(v, aes(x, y, colour = sig)) +
    geom_vline(xintercept = c(-fc_thresh, fc_thresh), linetype = "dashed",
               linewidth = 0.25, colour = nature_palette[["steel"]]) +
    geom_hline(yintercept = -log10(p_thresh), linetype = "dashed",
               linewidth = 0.25, colour = nature_palette[["steel"]]) +
    geom_point(data = subset(v, sig == "ns"), size = 0.5, alpha = 0.35) +
    geom_point(data = subset(v, sig != "ns"), size = 0.85, alpha = 0.85) +
    scale_color_manual(values = c(Up = nature_sig_col[["Up"]],
                                  Down = nature_sig_col[["Down"]],
                                  ns = nature_sig_col[["ns"]]),
                       breaks = c("Up", "Down", "ns"),   # 锁定图例顺序，防两层 geom 打乱
                       labels = c(Up   = sprintf("Up (n=%d)", n_up),     # 具名→标签绑对色块
                                  Down = sprintf("Down (n=%d)", n_dn),
                                  ns   = "ns"),
                       name = NULL) +
    labs(x = xlab, y = ylab, title = title, subtitle = subtitle) +
    theme(legend.position = c(0.99, 0.99), legend.justification = c(1, 1),
          legend.background = element_rect(fill = scales::alpha("white", 0.7), colour = NA))

  if (!is.null(label) && "lab" %in% colnames(v) && top_n > 0) {
    up <- subset(v, sig == "Up");   up <- up[order(-up$x), ][seq_len(min(top_n, nrow(up))), ]
    dn <- subset(v, sig == "Down"); dn <- dn[order(dn$x), ][seq_len(min(top_n, nrow(dn))), ]
    lab_df <- rbind(up, dn)
    if (requireNamespace("ggrepel", quietly = TRUE)) {
      p_out <- p_out + ggrepel::geom_text_repel(
        data = lab_df, aes(label = lab), size = 2.0, max.overlaps = 30,
        segment.size = 0.18, segment.colour = nature_palette[["steel"]],
        min.segment.length = 0, box.padding = 0.25, force = 1.5,
        colour = nature_palette[["ink"]], show.legend = FALSE)
    } else message("nature_volcano: 未装 ggrepel，跳过 top 基因标注。")
  }
  p_out
}

## ---- 富集 dotplot nature_enrich_dot() -------------------------------
# 兼容 clusterProfiler 输出：自动识别 score(FoldEnrichment/RichFactor/GeneRatio/NES)、
# p(p.adjust/qvalue/pvalue)、count(Count/setSize)。点大小=基因数，色深=-log10 p。
# 多库(GO/KEGG/Reactome)各画一个再 patchwork 拼（蓝本：figS1_enrichment.R）。
nature_enrich_dot <- function(df, term = "Description",
                              score = NULL, p = NULL, count = NULL,
                              top_n = 10, title = NULL, xlab = NULL, trunc = 46,
                              low = nature_sig_col[["Down"]], high = nature_sig_col[["Up"]]) {
  d <- as.data.frame(df)
  pick <- function(cands, given) if (!is.null(given)) given else {
    h <- intersect(cands, colnames(d)); if (length(h)) h[1] else NA_character_ }
  score_col <- pick(c("FoldEnrichment", "RichFactor", "GeneRatio", "NES"), score)
  p_col     <- pick(c("p.adjust", "padj", "qvalue", "pvalue", "p.val"), p)
  count_col <- pick(c("Count", "setSize", "overlap"), count)
  if (is.na(score_col) || is.na(p_col))
    stop("nature_enrich_dot: 找不到 score/p 列，请用 score=/p= 显式指定。")
  sv <- d[[score_col]]
  if (is.character(sv) && any(grepl("/", sv)))
    sv <- vapply(strsplit(sv, "/"), function(z) as.numeric(z[1]) / as.numeric(z[2]), numeric(1))
  else sv <- as.numeric(sv)
  if (is.na(count_col)) {
    if ("GeneRatio" %in% colnames(d)) { d$Count <- as.integer(sub("/.*", "", d$GeneRatio)); count_col <- "Count" }
    else { d$Count <- NA_real_; count_col <- "Count" }
  }
  ord <- order(as.numeric(d[[p_col]])); d <- d[ord, , drop = FALSE]; sv <- sv[ord]
  k <- seq_len(min(top_n, nrow(d)))
  lab <- make.unique(substr(trimws(gsub("\\s+", " ", d[[term]][k])), 1, trunc))
  pd <- data.frame(term  = factor(lab, levels = rev(unique(lab))),
                   x     = sv[k],
                   nlp   = -log10(pmax(as.numeric(d[[p_col]][k]), 1e-30)),
                   count = as.numeric(d[[count_col]][k]))
  if (is.null(xlab)) xlab <- if (identical(score_col, "NES")) "NES"
                             else if (grepl("Fold", score_col)) "Fold enrichment"
                             else if (identical(score_col, "GeneRatio")) "Gene ratio" else score_col
  ggplot(pd, aes(x, term, size = count, colour = nlp)) +
    geom_point() +
    scale_colour_gradient(low = low, high = high,
                          name = expression(-log[10]~adj.~italic(P))) +
    scale_size_continuous(name = "Gene count", range = c(1.5, 5),
                          breaks = scales::breaks_pretty(n = 3)) +
    labs(x = xlab, y = NULL, title = title)
}

## ---- KM 生存曲线 nature_km() ----------------------------------------
# 纯 survival+ggplot：自动算 Cox HR(95%CI)+log-rank p，画删失刻度，
# 可选「Number at risk」风险表（patchwork 拼下方，x 轴对齐）。
# 用法 A：df 含 time/status/group 三列；用法 B：给 value= 连续表达量，按 median 切 High/Low。
# 蓝本：纯 ggplot 生存脚本（HR+CI+双p+删失）⊕ survminer 风险表，二者并集。
nature_km <- function(df, time = "time", status = "status", group = "group",
                      value = NULL, split = "median", levels = NULL,
                      title = NULL, time_lab = "Time", surv_lab = "Survival probability",
                      legend_title = NULL,
                      cols = c(High = nature_sig_col[["High"]], Low = nature_sig_col[["Low"]]),
                      risk_table = TRUE, show_cox_p = TRUE) {
  if (!requireNamespace("survival", quietly = TRUE)) stop("nature_km 需要 survival 包")
  d <- as.data.frame(df)
  d$km_time   <- as.numeric(d[[time]])
  d$km_status <- as.integer(d[[status]])
  if (!is.null(value)) {
    vv  <- as.numeric(d[[value]])
    cut <- if (is.numeric(split)) split else stats::median(vv, na.rm = TRUE)
    d$km_grp <- factor(ifelse(vv > cut, "High", "Low"), levels = c("Low", "High"))
  } else {
    g <- d[[group]]
    d$km_grp <- if (is.null(levels)) factor(g) else factor(g, levels = levels)
  }
  d <- d[!is.na(d$km_time) & !is.na(d$km_status) & d$km_time >= 0 & !is.na(d$km_grp), ]
  glv <- levels(droplevels(d$km_grp)); d$km_grp <- factor(d$km_grp, levels = glv)

  fit <- survival::survfit(survival::Surv(km_time, km_status) ~ km_grp, data = d)
  sd  <- survival::survdiff(survival::Surv(km_time, km_status) ~ km_grp, data = d)
  lr_p <- 1 - stats::pchisq(sd$chisq, length(sd$n) - 1)
  sub <- NULL; cox_p <- NA_real_
  if (length(glv) == 2) {
    cox <- survival::coxph(survival::Surv(km_time, km_status) ~ km_grp, data = d)
    cs  <- summary(cox)
    hr  <- exp(stats::coef(cox))[1]; ci <- exp(stats::confint(cox))
    cox_p <- cs$coefficients[1, "Pr(>|z|)"]
    sub <- sprintf("HR %.2f (%.2f–%.2f)", hr, ci[1], ci[2])
  }

  s <- summary(fit)
  strat <- if (is.null(s$strata)) rep(glv[1], length(s$time)) else sub("^.*=", "", as.character(s$strata))
  kd <- data.frame(time = s$time, surv = s$surv, ncens = s$n.censor, grp = strat)
  kd <- rbind(data.frame(time = 0, surv = 1, ncens = 0, grp = glv), kd)
  kd$grp <- factor(kd$grp, levels = glv)
  tmax <- max(d$km_time, na.rm = TRUE)
  tt <- pretty(c(0, tmax), n = 6); tt <- tt[tt <= tmax]

  lab_p <- if (isTRUE(show_cox_p) && !is.na(cox_p))
             sprintf("log-rank p = %.3g | Cox p = %.3g", lr_p, cox_p)
           else sprintf("log-rank p = %.3g", lr_p)
  p_km <- ggplot(kd, aes(time, surv, colour = grp)) +
    geom_step(linewidth = 0.6) +
    geom_point(data = subset(kd, ncens > 0), shape = 3, size = 1.2, stroke = 0.6,
               show.legend = FALSE) +
    scale_color_manual(values = cols, name = legend_title) +
    scale_x_continuous(limits = c(0, tmax), breaks = tt) +
    scale_y_continuous(limits = c(0, 1), expand = expansion(mult = c(0.02, 0.04))) +
    annotate("text", x = 0, y = 0.06, hjust = 0, size = 2.2, label = lab_p) +
    labs(x = time_lab, y = surv_lab, title = title, subtitle = sub) +
    theme(legend.position = "top")

  if (!isTRUE(risk_table)) return(p_km)
  if (!requireNamespace("patchwork", quietly = TRUE)) {
    message("nature_km: 未装 patchwork，省略风险表。"); return(p_km)
  }
  sf <- summary(fit, times = tt, extend = TRUE)
  rstrat <- if (is.null(sf$strata)) rep(glv[1], length(sf$time)) else sub("^.*=", "", as.character(sf$strata))
  rt <- data.frame(time = sf$time, grp = factor(rstrat, levels = glv), n = sf$n.risk)
  p_rt <- ggplot(rt, aes(time, grp, label = n, colour = grp)) +
    geom_text(size = 2.2, show.legend = FALSE) +
    scale_color_manual(values = cols) +
    scale_x_continuous(limits = c(0, tmax), breaks = tt) +
    scale_y_discrete(limits = rev(glv)) +
    labs(x = NULL, y = NULL, title = "Number at risk") +
    theme(plot.title = element_text(size = 7, face = "plain"),
          axis.line = element_blank(), axis.ticks = element_blank(),
          axis.text.x = element_blank(), panel.grid = element_blank())
  patchwork::wrap_plots(p_km, p_rt, ncol = 1, heights = c(4, 1))
}

## ---- 分组配色 helper ------------------------------------------------
`%||%` <- function(a, b) if (is.null(a)) b else a

# 给一组分组名自动配色：命中语义名(Tumor/Normal/High/Low/Up/Down)用语义色，
# 其余按 nature_pal_6 循环。返回 named 向量。
nature_group_cols <- function(levels) {
  out <- setNames(rep(NA_character_, length(levels)), levels)
  for (l in levels) if (l %in% names(nature_sig_col)) out[[l]] <- nature_sig_col[[l]]
  pool <- nature_pal_6; i <- 1
  for (l in levels) if (is.na(out[[l]])) { out[[l]] <- pool[((i - 1) %% length(pool)) + 1]; i <- i + 1 }
  out
}

## ---- PCA / 降维散点 nature_pca() ------------------------------------
# 蓝本：fig1a_qc_pca.R —— 95% 置信椭圆 + 语义配色 + 半透明点。
# var_explained=c(PC1=..,PC2=..) 则自动把方差百分比写进轴标题。
nature_pca <- function(df, x = "PC1", y = "PC2", group = "group",
                       ellipse = TRUE, level = 0.95, cols = NULL, labels = NULL,
                       title = NULL, subtitle = NULL, xlab = NULL, ylab = NULL,
                       var_explained = NULL, point_size = 1.0) {
  df <- as.data.frame(df)
  d <- data.frame(px = as.numeric(df[[x]]), py = as.numeric(df[[y]]),
                  pg = factor(df[[group]]))
  glv <- levels(d$pg)
  if (is.null(cols)) cols <- nature_group_cols(glv)
  ax <- function(p) if (!is.null(var_explained) && p %in% names(var_explained))
                      sprintf("%s (%.1f%%)", p, var_explained[[p]]) else p
  p <- ggplot(d, aes(px, py, colour = pg, fill = pg))
  if (ellipse) p <- p + stat_ellipse(geom = "polygon", level = level,
                                      linewidth = 0.3, alpha = 0.10, show.legend = FALSE)
  p + geom_point(size = point_size, alpha = 0.85, shape = 16) +
    scale_color_manual(values = cols, name = NULL, labels = labels %||% glv) +
    scale_fill_manual(values = cols, guide = "none") +
    labs(x = xlab %||% ax(x), y = ylab %||% ax(y),
         title = title, subtitle = subtitle) +
    theme(legend.position = c(0.02, 0.98), legend.justification = c(0, 1),
          legend.background = element_rect(fill = scales::alpha("white", 0.7), colour = NA))
}

## ---- 箱线图 + jitter + 显著性 nature_box_sig() ----------------------
# 蓝本：04_immune_landscape_analysis.R —— 箱线+抖点+组间检验括号。
# 默认对所有两两组合做 Wilcoxon，画显著性括号（需 ggsignif）；缺包则退化为全局 Kruskal p。
nature_box_sig <- function(df, x = "group", y = "value", cols = NULL,
                           comparisons = NULL, test = "wilcox.test",
                           signif_stars = TRUE, jitter = TRUE,
                           title = NULL, xlab = NULL, ylab = NULL) {
  d <- data.frame(g = factor(df[[x]]), y = as.numeric(df[[y]]))
  d <- d[!is.na(d$y) & !is.na(d$g), ]
  glv <- levels(droplevels(d$g)); d$g <- factor(d$g, levels = glv)
  if (is.null(cols)) cols <- nature_group_cols(glv)
  p <- ggplot(d, aes(g, y, colour = g)) +
    geom_boxplot(aes(fill = g), alpha = 0.18, outlier.shape = NA,
                 linewidth = 0.4, width = 0.6)
  if (jitter) p <- p + geom_jitter(width = 0.18, size = 0.7, alpha = 0.5, show.legend = FALSE)
  p <- p + scale_color_manual(values = cols, guide = "none") +
    scale_fill_manual(values = cols, guide = "none") +
    labs(x = xlab, y = ylab %||% y, title = title)
  if (is.null(comparisons) && length(glv) >= 2)
    comparisons <- utils::combn(glv, 2, simplify = FALSE)
  if (length(comparisons) && requireNamespace("ggsignif", quietly = TRUE)) {
    p <- p + ggsignif::geom_signif(comparisons = comparisons, test = test,
                                   map_signif_level = signif_stars,
                                   step_increase = 0.08, textsize = 2.2,
                                   tip_length = 0.01, colour = nature_palette[["ink"]])
  } else if (length(glv) >= 2) {
    pv <- tryCatch(stats::kruskal.test(y ~ g, d)$p.value, error = function(e) NA)
    if (!is.na(pv)) {
      p <- p + labs(subtitle = sprintf("Kruskal–Wallis p = %.3g", pv))
      if (!requireNamespace("ggsignif", quietly = TRUE))
        message("nature_box_sig: 未装 ggsignif，改用全局 Kruskal p（无两两括号）。")
    }
  }
  p
}

## ---- Cox 森林图 nature_forest() -------------------------------------
# 配合已有 format_hr_label()/scale_x_hr_log()。输入 tidy df：term/HR/lo/hi/p。
# 点按是否显著着色，HR=1 处虚线，x 轴 log10。
nature_forest <- function(df, term = "term", hr = "HR", lo = "lo", hi = "hi", p = "p",
                          title = NULL, xlab = "Hazard ratio (95% CI)",
                          order_by_hr = TRUE, sig_level = 0.05, xlim = NULL,
                          show_label = TRUE) {
  d <- data.frame(term = as.character(df[[term]]),
                  hr = as.numeric(df[[hr]]), lo = as.numeric(df[[lo]]),
                  hi = as.numeric(df[[hi]]), p = as.numeric(df[[p]]),
                  stringsAsFactors = FALSE)
  ord <- if (order_by_hr) order(d$hr) else rev(seq_len(nrow(d)))
  d$term <- factor(d$term, levels = d$term[ord])
  d$sig <- factor(ifelse(d$p < sig_level, "sig", "ns"), levels = c("sig", "ns"))
  rng <- if (is.null(xlim)) range(c(d$lo, d$hi, 1), na.rm = TRUE) else xlim
  d$lab <- sprintf("%.2f (%.2f–%.2f)", d$hr, d$lo, d$hi)   # 建图前算好，否则图层拿不到
  p_out <- ggplot(d, aes(hr, term, colour = sig)) +
    geom_vline(xintercept = 1, linetype = "dashed", linewidth = 0.3,
               colour = nature_palette[["steel"]]) +
    geom_segment(aes(x = lo, xend = hi, y = term, yend = term), linewidth = 0.4) +
    geom_point(size = 1.9) +
    scale_colour_manual(values = c(sig = nature_sig_col[["Up"]], ns = nature_palette[["steel"]]),
                        breaks = c("sig", "ns"),
                        labels = c(sig = sprintf("p < %.2g", sig_level), ns = "ns"),
                        name = NULL) +
    scale_x_continuous(trans = "log10", limits = rng) +
    labs(x = xlab, y = NULL, title = title)
  if (show_label) {
    p_out <- p_out + geom_text(aes(x = rng[2], label = lab), hjust = 1,
                               size = 1.9, colour = nature_palette[["graphite"]],
                               show.legend = FALSE)
  }
  p_out
}

## ---- 突变全景 nature_oncoprint() (ComplexHeatmap::oncoPrint) ---------
# mat：基因×样本字符矩阵，单元格为 "" 或分号分隔的变异类型（如 "MUT;AMP"）。
# 默认配色与 alter_fun：CNV(AMP/DEL)铺满格、点突变类(MUT/TRUNC/FUSION)画中间细条。
nature_oncoprint <- function(mat, col = NULL, alter_fun = NULL,
                             title = NULL, ...) {
  if (!requireNamespace("ComplexHeatmap", quietly = TRUE)) stop("nature_oncoprint 需要 ComplexHeatmap 包")
  if (is.null(col))
    col <- c(AMP = "#D24B40", DEL = "#3775BA", MUT = "#3F8E4E",
             TRUNC = "#272727", FUSION = "#E28E2C")
  if (is.null(alter_fun)) {
    big <- function(fill) function(x, y, w, h)
      grid::grid.rect(x, y, w * 0.9, h * 0.9, gp = grid::gpar(fill = fill, col = NA))
    bar <- function(fill) function(x, y, w, h)
      grid::grid.rect(x, y, w * 0.9, h * 0.33, gp = grid::gpar(fill = fill, col = NA))
    full <- intersect(c("AMP", "DEL"), names(col))     # CNV 铺满
    thin <- setdiff(names(col), full)                  # 点突变类细条
    alter_fun <- c(
      list(background = function(x, y, w, h)
        grid::grid.rect(x, y, w * 0.9, h * 0.9, gp = grid::gpar(fill = "#ECECEC", col = NA))),
      setNames(lapply(full, function(k) big(col[[k]])), full),
      setNames(lapply(thin, function(k) bar(col[[k]])), thin)
    )
  }
  ComplexHeatmap::oncoPrint(
    mat, alter_fun = alter_fun, col = col,
    column_title = title, column_title_gp = nature_hm_gp(7, "bold"),
    row_names_gp = nature_hm_gp(6, "italic"),
    pct_gp = nature_hm_gp(6),
    heatmap_legend_param = list(title = "Alteration",
                                at = names(col), labels = names(col),
                                title_gp = nature_hm_gp(6.2, "bold"),
                                labels_gp = nature_hm_gp(5.8)),
    ...)
}
