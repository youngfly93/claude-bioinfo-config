# 生信反馈回路构造法

目标：得到一个**几秒内、确定、代理自己能跑**的"通过/失败"信号。下面按优先级给构造方式 + 可直接改用的代码骨架。

---

## 1. 失败的最小脚本

把触发 bug 的逻辑从大流程里抠出来，做成一个能独立跑的脚本 + 固定输入。脱离整条 pipeline 后，迭代速度从分钟级降到秒级。

```bash
Rscript -e 'source("R/deg.R"); x <- readRDS("fixtures/mini.rds"); print(run_deg(x))'
python -c 'import mod; print(mod.f(load_fixture()))'
```

## 2. 小数据 fixture

把数据砍到能秒级复现且仍触发 bug 的最小子集，存成固定文件，反复用。

```r
# R：抽 100 个高变基因 + 每组 3 个样本
set.seed(1)
mini <- se[head(order(-rowVars(assay(se))), 100),
           c(head(which(se$group=="A"),3), head(which(se$group=="B"),3))]
saveRDS(mini, "fixtures/mini.rds")
```
```python
# Python / scanpy
mini = adata[adata.obs.sample(n=200, random_state=1).index, :300].copy()
mini.write("fixtures/mini.h5ad")
```

## 3. 中间表快照

把关键中间对象存盘，改代码后 diff——精确定位"从哪一步开始数字变了"。

```r
saveRDS(dds, "snap/dds_before.rds")
# 改代码后
a <- readRDS("snap/dds_before.rds"); b <- dds
all.equal(assay(a), assay(b))           # 哪里变了
waldo::compare(rownames(a), rownames(b)) # 行名/顺序差异
```
```bash
# 表格类直接 diff（先排序消除顺序噪声）
sort old_deg.tsv > /tmp/a; sort new_deg.tsv > /tmp/b; diff /tmp/a /tmp/b | head
```

## 4. 旧 ↔ 新差分（differential loop）

同一输入跑两个版本（旧 commit / 旧参数 / 旧包），diff 关键数值。最适合"以前对、现在不对"。

用**临时 git worktree** 跑旧版本，不动当前工作区——比 `git stash`/`stash pop` 安全，不会和未提交改动冲突。

```bash
# 在隔离目录里检出旧版本，当前工作区原样不动
git worktree add /tmp/old-ver <known-good-commit>
Rscript /tmp/old-ver/run.R fixtures/mini.rds > /tmp/old.tsv   # 旧版本
Rscript run.R               fixtures/mini.rds > /tmp/new.tsv   # 当前版本
diff <(sort /tmp/old.tsv) <(sort /tmp/new.tsv)
git worktree remove /tmp/old-ver                              # 用完清理
```
```r
# 比 DEG 集合差异
setdiff(old$gene[old$padj<0.05], new$gene[new$padj<0.05])
```

## 5. 数值不变量断言

断言"该成立的关系"，而非具体值——对数据改动不脆，抓的是真 bug。

```r
stopifnot(
  !anyNA(res$padj[res$baseMean > 0]),        # 表达基因不应有 NA padj
  all(res$padj >= res$pvalue, na.rm = TRUE),  # padj ≥ p
  nrow(res) == nrow(dds),                     # 维度守恒
  identical(colnames(mat), rownames(meta))    # 样本对齐（最常见的坑）
)
```

## 6. git bisect

结果在两个已知状态之间变坏了，自动化二分。把"跑 + 判定"写成退出码脚本即可。

```bash
cat > /tmp/check.sh <<'EOF'
#!/bin/bash
Rscript run.R fixtures/mini.rds > /tmp/out.tsv || exit 125  # 跑不了→skip
n=$(awk 'NR>1 && $6<0.05' /tmp/out.tsv | wc -l)
[ "$n" -gt 100 ]   # 期望 >100 个 DEG，否则判失败
EOF
chmod +x /tmp/check.sh
git bisect start HEAD <known-good-commit>
git bisect run /tmp/check.sh
```

## 7. 性能打点 / profiling

```r
Rprof("prof.out"); res <- slow_fn(x); Rprof(NULL); summaryRprof("prof.out")
profvis::profvis(slow_fn(x))          # 交互火焰图
system.time(slow_fn(x))               # 粗粒度
```
```python
import cProfile; cProfile.run("slow_fn(x)", sort="cumtime")
```
```bash
# Nextflow / Snakemake：看每步耗时
nextflow run main.nf -with-trace -with-report report.html
snakemake --benchmark-extended   # 配合 rule 内 benchmark:
```

## 8. HITL 脚本（最后手段）

必须人在服务器上操作（如交互式登录、GUI 点击）时，用结构化脚本驱动人，把输出回流给代理，保持回路结构化。能自动化的绝不用这条。

---

## 通用纪律

- **先固定随机种子**（`set.seed`/`random_state`/`--seed`），否则你在追一个会变的目标。
- **隔离环境**：在 `renv`/conda env 里复现，排除"本地能跑服务器不能跑"的版本漂移。
- **一次只改一个变量**，每次都用回路确认，否则信号被污染。
- **缓存 setup**：数据加载/参考索引等不变的部分缓存掉，让每轮迭代只跑可疑那段。
