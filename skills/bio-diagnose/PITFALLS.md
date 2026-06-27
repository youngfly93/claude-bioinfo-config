# 生信高频 root cause 速查

"结果诡异/对不上/不可复现"的真实病因，绝大多数落在下面这些里。提假设时先逐条排查——便宜、命中率高。

## 数据对齐与 ID

- **样本错位**：表达矩阵的列顺序 ≠ metadata 的行顺序。最高频的坑。
  - 查：`identical(colnames(mat), rownames(meta))`；不等就 `mat <- mat[, rownames(meta)]`。
- **行列转置**：样本被当成基因（行/列搞反），常见于读 CSV 后忘了转置。
  - 查：`dim()` + 看 `rownames`/`colnames` 是不是基因还是样本。
- **基因 ID 映射**：Ensembl 版本不一致、`ENSG` 带不带版本号后缀（`.12`）、symbol 多对一去重策略不同。
  - 查：映射前后行数变化、`duplicated(symbol)`、`anyNA(mapped_id)`。
- **join 引入 NA / 行数膨胀**：`merge`/`left_join` 键不唯一导致行数暴涨或产生 NA。
  - 查：join 前后 `nrow`、键的 `duplicated()`。

## 分组与设计

- **参考组方向反了**：因子默认按字母序，"control" 可能不是参考水平，导致 logFC 符号全反。
  - 查/修：`relevel(group, ref="control")` 或 `factor(levels=...)`；确认 contrast 写的是 `treat - control`。
- **批次与分组混杂**：批次校正把真信号一起抹掉，或没校正导致假阳性。
  - 查：PCA 上色看批次 vs 分组是否共线。
- **协变量当成数值/因子搞错**：把分组编码成 1/2 当连续变量喂模型。

## 数值与统计

- **NA 传播**：上游一个 NA 导致下游整列/整行变 NA（`sum`/`cor` 未设 `na.rm`）。
  - 查：`colSums(is.na(x))`、`stopifnot(!anyNA(...))`。
- **count vs 归一化值喂错**：把 TPM/FPKM/log 值喂给要 raw count 的 DESeq2/edgeR；或把 count 直接画 PCA。
- **log/伪计数**：`log(0)`= -Inf；忘了 `+1` 伪计数；log 底数不一致（自然对数 vs log2）。
- **过滤时机**：在归一化之后才过滤低表达，或独立过滤与显式过滤叠加导致结果飘。
- **多重检验**：用 p 而非 padj 卡阈值；或对已校正值再校正。

## 可复现性与环境

- **随机种子未固定**：聚类、UMAP、采样、ML、`sample()` 每次结果不同。
  - 修：`set.seed()` / `random_state=` / pipeline `--seed`，且放在随机调用紧邻之前。
- **包版本漂移**：本地能跑、服务器(<compute-server>)结果不同，多因 DESeq2/Seurat/edgeR 版本不同改了默认行为。
  - 查：两端 `sessionInfo()` 对比；用 `renv.lock`/conda env 锁定。
- **工作目录 / 相对路径**：`Rscript` 与交互式 R 的 `getwd()` 不同导致读错文件或读到旧文件。
- **缓存/中间文件过期**：读到上一次跑的旧 `.rds`/中间表，改了上游却没重跑。
  - 查：中间文件的 `mtime` 是否晚于上游脚本。

## 单细胞专属

- 线粒体基因前缀大小写（`^MT-` vs `^mt-`，人 vs 鼠）导致 QC 过滤失效。
- 整合前后用错 assay（在 `integrated` 上做差异、或在 `SCT` 残差上当表达量）。
- 分辨率/PC 数变化导致聚类数突变——不是 bug，是参数敏感，需固定并记录。

## 性能 / 资源

- **在循环里增长对象**（`x <- rbind(x, ...)`）→ O(n²)。改预分配或 `do.call`/`data.table`。
- **未向量化** / apply 套 apply。
- **OOM**：大矩阵稠密化（稀疏转稠密）、一次性读入超大文件。改分块/稀疏/`data.table::fread`。
- **并行反而更慢**：fork 开销 > 收益，或嵌套并行抢核。

---

> 排查命中后，按 [SKILL.md](./SKILL.md) 阶段 6 把它固化成不变量断言或快照，防止复发。
