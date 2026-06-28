# 已知摩擦点与防护规则

> 从 116 个历史 session（buggy code 83次、wrong approach 49次）中提炼。
> 遇到问题时查阅此文件，看是否命中已知模式。

---

## Top 10 高频错误

| # | 问题 | 防护规则 | 严重度 |
|---|------|---------|--------|
| 1 | 报告数值与源数据不一致 | 所有数值程序化从源文件提取，禁止手动输入 | P0 |
| 2 | scRNA-seq cluster 注释错误 | 注释后展示 top5 marker 并与文献交叉验证 | P0 |
| 3 | bash 脚本在 macOS 3.x 上失败 | 禁止 `declare -A`、禁止 bash 4+ 特性 | P1 |
| 4 | ORA DEG 定义与 plan.md 阈值不一致 | DEG 过滤必须引用 plan.md 中的固定参数 | P1 |
| 5 | python-docx 行号偏移崩溃 | 段落内容匹配，非行号定位 | P1 |
| 6 | 修改脚本后未重跑下游步骤 | 每次修改后检查 output 时间戳是否 stale | P1 |
| 7 | git commit 被 .gitignore 阻止 | 提交前检查 .gitignore | P2 |
| 8 | 方法选择错误导致返工 | 复杂任务先输出 3-5 点方法概要，等确认 | P2 |
| 9 | 会话止于规划不执行 | plan 完成后立即进入执行，不等二次确认 | P2 |
| 10 | AI 关键词残留在交付文件中 | 打包前强制扫描（`harness/delivery/ai_scan.sh`） | P1 |

---

## 分析类型特有防护

### scRNA-seq
- 禁止在未验证 annotation 准确性前进行下游分析
- Harmony 整合后必须重新检查 cluster 结构
- inferCNV 参考细胞选择需要记录理由
- FindMarkers 的 ident.1/ident.2 方向要明确

### Bulk RNA-seq
- DESeq2 输入必须是 raw counts（检查是否有小数）
- 对照组必须在 design formula 的 reference level
- 富集分析 gene list 和 background 的定义必须明确
- 修改上游脚本后检查下游 output 时间戳

### 报告生成
- 每张图的 figure legend 必须描述实际展示的内容
- 表格中的 p-value 显示精度统一
- 页眉页脚不得包含 AI 工具名称
- python-docx 编辑用段落匹配，不用行号

### 多组学
- 各组学数据的样本 ID 匹配验证是第一步
- 不同组学的归一化方法不能混用
- 整合分析前各单组学必须独立验证通过

---

## 环境陷阱

| 问题 | 表现 | 修复 |
|------|------|------|
| macOS bash 3.x | `declare -A` 报错、`set -u` + 数组异常 | 用简单变量替代关联数组 |
| R 包版本冲突 | Bioconductor 版本与 R 版本不匹配 | 检查 BiocManager::version() |
| python-docx XML | 保存后行号偏移 | 永远用内容匹配 |
| GEO 数据已 normalized | DESeq2 结果异常（variance 极小） | 检查 GEO Data Processing 说明 |
| Tailscale 连接断开 | 文件传输失败 | 检查 `tailscale status` |
