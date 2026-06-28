---
name: bio-deliver
description: >-
  生信项目完整交付的唯一总入口：质量审计→报告/图表检查→文件收集→AI痕迹扫描→ZIP打包→验证。
  需要完整交付、打包、发客户、出包时优先使用本 skill；它可编排 bio-result-audit、bio-report、bio-fig-review、bio-ai-clean 等专项能力。
  触发条件：用户说"交付"、"打包"、"deliver"、"发给客户"、"出包"。
  不适用于：仅需部分文件复制、只需生成报告/审图/清 AI 痕迹的专项场景、非项目交付场景。
---

# 交付打包

`bio-deliver` 是生信项目完整交付的总入口。只要目标是“发给客户/打包/出包”，优先从这里启动；`bio-result-audit`、`bio-report`、`bio-fig-review`、`bio-ai-clean` 作为专项能力被本流程按需调用，而不是让用户在交付时手动串联多个 skill。

## Tool Facet — 确定性操作

本 skill 提供两个独立工具脚本，位于 skill 目录的 `scripts/` 下。

在 Claude Code 中通常可用 `${CLAUDE_SKILL_DIR}`。在 Codex 或其他环境中若该变量不存在，先设置：

```bash
SKILL_DIR="~/.codex/skills/bio-deliver"
```

下面命令中的 `${SKILL_DIR}` 可替换为 `${CLAUDE_SKILL_DIR}`。

### zip_pack.py

```bash
# 打包
python3 ${SKILL_DIR}/scripts/zip_pack.py pack <delivery_dir> [项目名]
# → {"zip_path": "..."}

# 验证
python3 ${SKILL_DIR}/scripts/zip_pack.py verify <zip_path>
# → {"crc_ok": true, "file_count": N, "total_size_mb": N, "files": [...]}

# 校验和
python3 ${SKILL_DIR}/scripts/zip_pack.py checksum <delivery_dir>
# → {"checksum_path": "..."}
```

### ai_trace_scan.py

```bash
# 扫描
python3 ${SKILL_DIR}/scripts/ai_trace_scan.py scan <directory>
# → JSON 数组，每项 {"file": "...", "type": "metadata|content", "match": "..."}
# 退出码: 0=无痕迹, 1=发现痕迹

# 清除
python3 ${SKILL_DIR}/scripts/ai_trace_scan.py clean <directory>
# → JSON 数组，每项 {"file": "...", "cleaned_count": N}
```

---

## Prompt Facet — 流程决策指导

### 边界（CONSTRAINT）

- 步骤 1→8 顺序执行，不可跳步；按需项没有适用文件时标记为“不适用”
- 步骤 1 有 P0/P1 问题 → 中止打包，建议先执行审计修复流程
- ZIP 打包和 AI 扫描必须调用上方 Tool Facet 脚本，不可内联重写
- 排除文件：.DS_Store, __MACOSX, .git, .Rhistory, .RData, Thumbs.db
- **过程记录不进交付包**：`HANDOFF.md`、`DOCS_INDEX.md`、`execution_log.md`、`fix_log.md`、`audit/`、`.work/`、`_archive/`、各类 `*_v*` / `*_final` / 草稿 md——这些是内部记录，客户包只放正式报告/图/表/脚本/溯源表。源目录散落多版本 md 太多 → 先用 `bio-docs-tidy` 收口再打包。
- 必须有 plan.md 才能启动（无则停止，提醒先建立）
- ZIP 文件名格式：`项目名_交付_YYYYMMDD.zip`
- **版本纪律（防泛滥 + 防改错目录）**：只在一个正本目录构建交付物；出新版时把旧版归档到 `_archive/`，并用 `delivery_latest` 软链指向当前正本；绝不在 `.tmp*`、`xxx 2`/`xxx 3`、副本目录里改。每次只操作正本。
- **抗崩溃**：Step 1 审计按模块落盘（见 `bio-result-audit`）；Step 3 收集边复制边把清单追加到 `delivery_manifest.tsv`。中途撞 token 上限/超时后可从 manifest 续传，不从头重来。

  #### 在此边界内追求（ASPIRATION）

  以下所有追求不得违反上方边界。

  - AI 痕迹彻底清除（宁多扫不遗漏）
  - Windows 兼容性（中文文件名不乱码）
  - 交付物结构规范：按下方「交付目录标准结构（主题优先）」组织，主题编号即阅读顺序，每个主题内图/表物理隔离
  - Word 文档完整性经过验证（图片引用、XML 结构、中文字体）

    ##### 可自主决定（FREEDOM）

    以下选择空间在上方边界和追求方向内自主发挥。

    - 已有 delivery/ 时覆盖还是增量（询问用户）
    - P2/P3 问题的处理方式（警告继续 vs 先修复）
    - `NN_分析代码/` 是否包含（根据项目判断）
    - 主题如何切分与命名、主题编号顺序（按分析逻辑判断）

### 交付目录标准结构（主题优先）

`delivery/项目名_交付_YYYYMMDD/` 下按下面结构组织：客户友好、图/表/脚本物理隔离、可一路溯源。

```
项目名_交付_YYYYMMDD/
├── 00_交付说明.pdf        # 导航：目录说明 + 分析概览 + 怎么读这个包 + 联系方式
├── 01_分析报告/           # 正式 Word/PDF 报告（客户第一眼看的）
├── 02_质控/               # 一个分析主题 = 一个编号文件夹（自包含）
│   ├── 图/                # 该主题高清图（PNG/PDF/TIFF）
│   └── 表/                # 该主题结果表（CSV/XLSX）
├── 03_差异表达/
│   ├── 图/
│   └── 表/
├── 04_富集分析/
│   ├── 图/
│   └── 表/
├── ...                    # 主题按分析逻辑顺序编号递增
├── NN_分析代码/           # 倒数第二个编号：编号脚本（按执行顺序）+ README_脚本说明.md
└── NN_溯源表.xlsx         # 最后一个编号：结果/图 → 源数据 → 生成脚本
```

约定：
- 主题文件夹编号从 `02` 起，按执行/逻辑顺序排（质控→差异→富集→…），**编号即阅读顺序**。
- 每个主题内部固定分 `图/`、`表/` 两个子目录，图和表物理隔离。
- `NN_分析代码/` 放编号脚本（`01_*.R`、`02_*.R`…）与 `README_脚本说明.md`：逐脚本写明 输入 → 做什么 → 输出到哪个主题。
- `NN_溯源表.xlsx`：每个承重结果/图一行，列为 `结果/图(路径) | 所属主题 | 源数据(文件:列) | 生成脚本 | 关键参数/阈值`，让客户与你都能从交付物追回源头；与 `bio-result-audit` 的数字台账互为印证。

### 步骤

**Step 1 — 质量审计（门控，含数字台账）**
对照 `plan.md` 做质量审计；交付前审计**必须包含** `bio-result-audit` 的「关键 claim 复算与数字台账」——承重的每个数字/结论从源数据独立复算对账（方向/符号、统计量、逐字三类都查），任一不一致即 P0/P1 中止打包。Codex 中使用 `bio-result-audit` skill；Claude Code 中也可以使用 `bio-result-auditor` agent。

**Step 2 — 报告/图表专项检查（按需）**
若需要生成或修订 Word 报告，使用 `bio-report`；若交付物已包含 Word 报告，按 `bio-report` 的验证规则检查 XML、图片引用、Markdown 残留和中文格式。若交付物包含图表，按 `bio-fig-review` 检查分辨率、标签、图例、配色、统计标注和图表-数据一致性。

**Step 3 — 收集交付物并组织标准结构**
按 plan.md 确定文件，复制到 `delivery/项目名_交付_YYYYMMDD/`，严格按上方「交付目录标准结构（主题优先）」组织：报告进 `01_分析报告/`；每个分析主题建 `NN_主题/`，图、表分别放入其 `图/`、`表/`；脚本进 `NN_分析代码/`。不复制中间文件（.RData, .rds）和原始数据（fastq, bam）。同时生成三份导航/溯源产物：
- `00_交付说明`：目录导航 + 分析概览 + 怎么读这个包 + 联系方式；
- `NN_溯源表.xlsx`：承重结果/图逐条，列含 结果/图路径、所属主题、源数据(文件:列)、生成脚本、关键参数/阈值；
- `NN_分析代码/README_脚本说明.md`：逐脚本写明 输入 → 处理 → 输出到哪个主题。

**Step 4 — AI 痕迹扫描**
调用 `ai_trace_scan.py delivery/`。发现 → 修复 → 重扫确认。

**Step 5 — Word 文档验证**
AI 痕迹处理后，再次检查 .docx 图片引用、XML 完整性、中文字体。

**Step 6 — 校验和**
调用 `zip_pack.py checksum delivery/`

**Step 7 — 打包**
调用 `zip_pack.py pack delivery/ 项目名`

**Step 8 — 验证**
调用 `zip_pack.py verify <zip_path>`

### 最终输出

```
| 步骤 | 状态 | 详情 |
|------|------|------|
| 1. 质量审计 | ✅/❌ | P0:0 P1:0 P2:N P3:N |
| 2. 报告/图表检查 | ✅/⚠️/N/A | 报告 N 个，图表 N 个 |
| 3. 文件收集+标准结构 | ✅ | N 文件, XX MB, 主题 N 个 |
| 3b. 溯源表/交付说明 | ✅ | 溯源 N 条, 交付说明 ✓ |
| 4. AI痕迹 | ✅/⚠️ | 清除 N 处 |
| 5. Word验证 | ✅/❌/N/A | N 个文档通过 |
| 6. 校验和 | ✅ | delivery_md5.txt |
| 7. ZIP打包 | ✅ | 文件名 |
| 8. ZIP验证 | ✅ | CRC通过, N 文件 |

ZIP路径: xxx
ZIP大小: xx MB
```

## 交付后：发表支持（可选 · 衔接 nature-* 链）

客户拿到交付常要发论文——交付物里 `溯源表`/`report_claims.tsv`（可溯源数字）+ house 样式图 + `plan.md`（方法学）就是现成的论文素材。需要时按这条链走：

| 步 | skill | 用交付物里的什么 |
|---|---|---|
| 起草 | `nature-writing` | report_claims 数字 + 图 → Methods/Results/Intro |
| 补引用 | `nature-citation` | 给正文加严格 CNS 引用 |
| 润色 | `nature-polishing` | 中文/初稿 → Nature 英文 |
| 数据可用性 | `nature-data` | GEO/SRA 提交、Data Availability、FAIR |
| 审稿轮 | `bio-audit-fix` + `nature-response` | 重分析 + 逐点回复 |
| 汇报 | `nature-paper2ppt` / `bio-ppt` | 把分析讲清楚 |
