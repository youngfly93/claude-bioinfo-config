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
- **过程记录不进交付包（已机械强制）**：`HANDOFF.md`、`DOCS_INDEX.md`、`execution_log.md`、`fix_log.md`、`audit/`、`.work/`、`_archive/`、`proof.json`、`goal_proof.md`、`.bio_harness/`、`*.log`、`*.rds`/`*.RData` 等——`zip_pack.py` 的 `EXCLUDE`/`EXCLUDE_PATTERNS` 打包时**机械排除并打印排除清单**，不再靠收集时手工挑。客户包只放正式报告/图/表/脚本（+可选溯源表）。多版本 `*_v*`/`*_final` 草稿由 `dedup_check.py` 把关；散落 md 太多先 `bio-docs-tidy` 收口。
- **临床/敏感项目硬卡**：项目根放一个空文件 `.bio_clinical_mode` → 交付门 `delivery_gate` 强制 **strict**（缺 proof / 命令 exit≠0 / status 非 PASS 直接拦停 Stop，不只警告）。平时个人项目不放它=advisory 不卡手。
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
    - `分析代码/` 是否包含（根据项目判断）
    - 主题如何切分与命名、主题编号顺序（按分析逻辑判断）

### 交付目录标准结构（主题优先）

`delivery/项目名_交付_YYYYMMDD/` 下按下面结构组织：客户友好、图/表/脚本物理隔离、可一路溯源。**此结构由 Step 3.5 的 `structure_check.py` 打包前机器强制**（完整模板见 `harness/templates/delivery_structure.md`，可直接拷骨架）。

```
项目名_交付_YYYYMMDD/
├── README.md              # 唯一说明：分析概览 + 怎么读这个包 + 逐脚本说明 + 联系方式
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
├── 分析代码/              # 编号脚本（按执行顺序 01_*.R、02_*.R…）
└── 溯源表.xlsx            # 可选：结果/图 → 源数据 → 生成脚本（承重项建议保留）
```

约定（**少文档、命名易懂、只留必要**）：
- **文档只有根目录一份 `README.md`**——概览 + 怎么读 + 逐脚本说明（输入→做什么→输出到哪个主题）全并进去；**不再产 `00_目录导航.md`、不再放子目录 README**（结构本身够清晰，多份说明正是"AI 感"来源）。
- 主题文件夹编号从 `02` 起，按执行/逻辑顺序排（质控→差异→富集→…），**编号即阅读顺序**。
- 每个主题内部固定分 `图/`、`表/` 两个子目录，图和表物理隔离。
- `分析代码/` 放编号脚本（`01_*.R`、`02_*.R`…），命名见名知意；脚本说明在根 README，不另立文件。
- `溯源表.xlsx`（**可选保留**）：每个承重结果/图一行，列为 `结果/图(路径) | 所属主题 | 源数据(文件:列) | 生成脚本 | 关键参数/阈值`；与 `bio-result-audit` 的数字台账互为印证。

### 步骤

**Step 1 — 质量审计（门控，含数字台账）**
对照 `plan.md` 做质量审计；交付前审计**必须包含** `bio-result-audit` 的「关键 claim 复算与数字台账」——承重的每个数字/结论从源数据独立复算对账（方向/符号、统计量、逐字三类都查），任一不一致即 P0/P1 中止打包。Codex 中使用 `bio-result-audit` skill；Claude Code 中也可以使用 `bio-result-auditor` agent。

**Step 2 — 报告/图表专项检查（按需）**
若需要生成或修订 Word 报告，使用 `bio-report`；若交付物已包含 Word 报告，按 `bio-report` 的验证规则检查 XML、图片引用、Markdown 残留和中文格式。若交付物包含图表，按 `bio-fig-review` 检查分辨率、标签、图例、配色、统计标注和图表-数据一致性。

**Step 3 — 收集交付物并组织标准结构（只收必要，命名易懂）**
按 plan.md 确定文件，复制到 `delivery/项目名_交付_YYYYMMDD/`，严格按上方「交付目录标准结构（主题优先）」组织：报告进 `01_分析报告/`；每个分析主题建 `NN_主题/`，图、表分别放入其 `图/`、`表/`；脚本进 `分析代码/`。**只收能覆盖分析的必要文件：脚本 + 图 + 结果表 + 报告**；不复制中间文件（.RData/.rds/.log）、原始数据（fastq/bam）、过程记录（HANDOFF/execution_log/audit/.work/proof 等——已由 `zip_pack.py` 机械兜底排除，但收集时也别往里放）。产物只两份：
- **根 `README.md`（唯一说明文档）**：分析概览 + 怎么读这个包 + 逐脚本说明（输入→处理→输出到哪个主题）+ 联系方式。人写背景/口径，脚本说明可据 `分析代码/` 里各脚本头（`# 步骤/# 上游/# 输出`）汇总。
- `溯源表.xlsx`（**可选**）：承重结果/图逐条，列含 结果/图路径、所属主题、源数据(文件:列)、生成脚本、关键参数/阈值。

**Step 3.5 — 去冗余 + 结构校验（客户包要「结构清晰、无冗余、好找」）**
打包前两道机器 gate（均在 `${CLAUDE_PLUGIN_ROOT:-$HOME/.claude}/harness/delivery/` 下）：
- `dedup_check.py delivery/`：**P2（多版本 `_v2`/`_final`/副本/草稿残留）必须清零**，P3（内容完全相同的重复）复核——同一交付物只出现一次。
- `structure_check.py delivery/`：核对是否合「标准结构」——**P1（图/ 混进表、表/ 混进图、没报告）必拦**；P2（无 01_分析报告、主题没分图/表、根目录散文件）整改；P3（缺溯源表、编号跳号）。让客户结构清晰、一眼定位。根 `README.md`、`00_*`、`溯源表` 不算散文件。

**Step 4 — AI 痕迹 + 隐私扫描**
- AI 痕迹：调用 `ai_trace_scan.py delivery/`。发现 → 修复 → 重扫确认。
- **隐私红线**：调用 `${CLAUDE_PLUGIN_ROOT:-$HOME/.claude}/harness/delivery/privacy_scan.py delivery/`——扫本机路径(`/Users/`、`/home/`)、内网 IP、邮箱等客户/患者数据泄漏。**P0(路径/IP)必须清零**才放行；临床项目(`.bio_clinical_mode`)硬卡。

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
| 3b. 根 README（+可选溯源表） | ✅ | README ✓, 溯源 N 条 |
| 3.5 去冗余+结构校验 | ✅ | 排除过程文件 N 个, 结构 P1:0 |
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
