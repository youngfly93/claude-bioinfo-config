# Bio Skill 速查表

生信分析全流程的 skill 体系（Claude + Codex 双引擎，`~/.claude/skills/` + `~/.codex/skills/` 软链接同步）。
所有 bio 能力已统一为 `bio-*` / 独立 skill，原 `bio:` 插件命令已退役（备份在 `~/.claude/plugins/.retired-bio-*`）。

> 更新于 2026-06-27。

## 全流程闭环

```
建项目          画地图           开工对齐         执行调试
bio-project-init → bio-zoom-out → bio-grill  →  bio-diagnose
                                                     │
   交付打包        清 AI 痕迹       出报告      ┌────┴────┐
   bio-deliver  ←  bio-ai-clean  ← bio-report   审计      修复
        ↑                                   bio-result-audit / bio-audit-fix
        │              出图                      │
        └──────  bio-fig-review / nature-figure  │
                                                 ↓
                          产新见解 / 验证设计  bio-roundtable
```

## 速查表（按使用阶段）

| 阶段 | Skill | 一句话 | 触发词 | 不适用 → 改用 |
|------|-------|--------|--------|--------------|
| 建项目 | **bio-project-init** | 生成 plan.md/CLAUDE.md + 标准目录脚手架 | 初始化生信项目、建项目脚手架、新建外包项目 | 已有项目→bio-zoom-out |
| 接手/熟悉 | **bio-zoom-out** | 升一层，画项目地图（问题/管线/文件/进度，只读） | 梳理一下这个项目、这个目录是干嘛的、给我画张地图、升一层 | 已熟悉、跑某步→直接做 |
| 开工前 | **bio-grill** | 逐条审问分析设计，给推荐答案，出"设计确认单" | 审问我、开工前对齐、分析前检查、帮我盘一下这个分析 | 设计已定→直接执行 |
| 出错/异常/变慢 | **bio-diagnose** | 调试纪律：先建反馈回路→缩小→假设→插桩→修复→回归 | debug、跑不通、结果不对、数字对不上、pipeline 崩了、为什么这么慢 | 开工前对齐→bio-grill |
| 审计（只读） | **bio-result-audit** | 对照 plan.md 审计结果质量，出结构化报告（不改文件） | check、审计、检查结果、对照 plan.md、交付前检查 | 要修→bio-audit-fix |
| 审计+修复 | **bio-audit-fix** | 审计→分级 P0-P3→立即修复→提交→重审（≤5 轮，会改文件） | audit-fix、审计并修复、边审边修、把问题都修了 | 只读审计→bio-result-audit |
| 出图 | **bio-fig-review** | 批量审查已有图片是否达 SCI/交付标准（只审不画） | 审图、图表审查、这些图能交付吗 | 从头画图→nature-figure |
| 出图 | **nature-figure** | 投稿级出图工作流（R/Python 双后端，生成+审计+导出） | 画图、做主图、figure | 只审已有图→bio-fig-review |
| 报告 | **bio-report** | 生成中文 Word 交付报告（按 plan.md 组织，套排版规范） | 生成报告、出 Word 报告、写分析报告 | 论文稿件→nature-writing；PPT→ppt |
| 清 AI 痕迹 | **bio-ai-clean** | 扫除 AI 痕迹（HARD 自动清 / SOFT 只标记，单一真源脚本） | 清 AI 痕迹、去 AI 味、交付前清理 | 完整打包→bio-deliver |
| 交付 | **bio-deliver** | 一键打包：审计门控→收集→清痕迹→Word 验证→Win 兼容 ZIP | 交付、打包、发给客户、出包 | 仅复制部分文件→手动 |
| 产新见解 | **bio-roundtable** | 圆桌：从已有结果产新假说/新切口/验证方案（insight/validation） | 圆桌、roundtable、新见解、下一步验证 | 数据质量未确认时不用 |
| 贯穿·交接 | **bio-handoff** | 写/读交接棒：在制状态写进 HANDOFF.md，跨 /clear /compact 续接；含审核口径合同（审批只认它） | 交接、handoff、续上、clear/compact 前先记、换上下文接着干 | 快速 compact→save；从零建图→bio-zoom-out |

## 关键工程约定

- **AI 痕迹单一真源**：`~/.claude/skills/bio-deliver/scripts/ai_trace_scan.py`
  - HARD（工具名/第一人称自指/代码注释/Office 元数据）→ `clean` 自动清除
  - SOFT（综上所述/值得注意的是 等套话）→ 只 `scan` 标记 `action=review`，人工判断，**绝不自动删**
- **三层文档分工**（bio-grill / bio-diagnose 落档用）：
  - `CONTEXT.md` = 术语、样本命名、contrast 含义
  - `plan.md` = 分析步骤与进度
  - `docs/analysis-decisions/` = "为什么这样分析"（仅记：有人会反对 / 改回代价大 / 审稿客户会问）

## 与通用工具的边界
- 环境预检 → `preflight` ｜ 传文件到 Windows → `transfer` ｜ 做 PPT → `ppt`
- 会话交接 → `bio-handoff`（结构化·含审核口径合同）/ `save`（快速 compact）/ `now` ｜ 论文写作/润色/引用 → `nature-*` 全家桶

## 维护备注
- 新增/修改 bio skill 后，记得 `ln -s ~/.claude/skills/<name> ~/.codex/skills/<name>` 同步 Codex。
- `bio-result-audit` / `bio-fig-review` / `bio-project-init` 由并行会话创建；`bio-ai-clean` / `bio-audit-fix` / `bio-report` 与三个 `*-bio` 由本线创建——风格已对齐。
