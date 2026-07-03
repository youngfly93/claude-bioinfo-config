# Claude Code 环境配置 · 生信交付工作流

> 这是一份 **Claude Code 环境配置的精选 + 脱敏快照**，用于请人评估**配置设计本身**。
>
> ⚠️ **不含任何凭证、会话记录、客户/患者数据**——只有“设计产物”（规则 / 技能 / 钩子 / 样式）。
> 真实路径、用户名、服务器名、客户项目名已替换为 `~` / `<user>` / `<compute-server>` / `<project>` 等占位符。

## 作为插件安装

本库同时是一个 Claude Code **插件 + marketplace**（见 `.claude-plugin/`）：

```bash
/plugin marketplace add youngfly93/claude-bioinfo-config
/plugin install bio-delivery@youngfly93-bioinfo
```

> ⚠️ **可移植性**：钩子用 `${CLAUDE_PLUGIN_ROOT}`，可移植；但 skill 内部脚本（docx_check / house 样式等）路径假设装在 `~/.claude`（已脱敏为 `~`）。跨机一键即用需把这些引用也改成 `${CLAUDE_PLUGIN_ROOT}`——当前版本最适合"装进自家 `~/.claude` 或作参考"。

> 📦 **新机器 / Windows 配置**：装插件只给「能力」，不给「政策」（CLAUDE.md 规则不随插件走，要每台机器手写）——完整步骤见 **[`docs/SETUP.md`](docs/SETUP.md)**，工作区政策模板见 **[`docs/workspace.CLAUDE.example.md`](docs/workspace.CLAUDE.example.md)**。可直接交给目标机器的 Claude Code 照着配。

## 背景

一个生物信息工程师（癌症基因组 / 多组学 / 蛋白组 / 临床报告**外包交付**）的 Claude Code 工作环境。
设计目标：让交付**一次做对、全程一套风格、可溯源、中文安全、少返工**。

## 整体框架（三层）

```
生信交付工作环境
│
├─ ① 全局层  —— always-on，每会话/每项目自动生效
│  ├─ CLAUDE.md         全局原则（关于用户 / 绘图 / 科研严谨性）
│  ├─ settings.json     model / effort / 插件 / 钩子
│  ├─ hooks/            机械钩子，每条 Bash 自动跑
│  │   ├─ bash3_check.py            bash4 语法预警
│  │   ├─ cjk_shell_check.py        中文写文件 → 提醒用 Python
│  │   ├─ canonical_guard.py        改/删非正本目录 → 确认
│  │   └─ destructive_git_guard.py  不可逆 git 操作（reset --hard 等）→ 确认
│  └─ assets/figure-style/nature_theme.R   统一 house 样式（主题+热图+CJK安全）
│
├─ ② agents/  —— 自定义子代理（独立模型 + 独立上下文）
│   ├─ bio-result-auditor      只读审计代理
│   └─ bio-report-writer  ⚡固定 Opus 4.6  出报告（主会话模型不受影响）
│
└─ ③ Skill 层  —— 触发才生效（bio-* 家族，15 个）
   ├─ 开工      bio-project-init · bio-grill〔接文献检索〕
   ├─ 理解/调试 bio-zoom-out · bio-diagnose
   ├─ 审计/修复 bio-result-audit · bio-fig-review(⚙) · bio-audit-fix
   ├─ 报告      bio-report(⚙)
   ├─ 交付      bio-deliver(⚙ · 总入口) · bio-goal〔goal loop〕
   ├─ 汇报      bio-ppt(⚙)
   ├─ 接续/整理 bio-handoff · bio-docs-tidy
   └─ 其它      bio-ai-clean · bio-roundtable〔接文献检索〕
       ⚙ = 确定性脚本（docx_check / fig_check / zip_pack / ai_trace_scan / build_deck）
       ⚡ = 子代理钉死模型
```

## 目录说明

| 路径 | 作用 |
|---|---|
| `CLAUDE.md` | 全局规则，每会话注入；只放“所有项目都成立”的原则 |
| `settings.json` | 模型(opus[1m]) / 推理强度 / 启用插件 / PreToolUse 钩子 |
| `hooks/` | Bash/写入预检钩子：bash3 语法 · 中文写文件 · 非正本目录守护 · 不可逆 git 操作减速带 等 |
| `docs/` | 设计文档：goal-loop 原理 · 跨机配置(SETUP) · 工作区政策模板 · 写 skill 的尺子(WRITING-SKILLS) · 双 agent 审计标准(SHARED-AUDIT) |
| `assets/figure-style/nature_theme.R` | 统一绘图样式真源：ggplot 主题 + 语义配色 + ComplexHeatmap 热图 + CJK 安全字体自动解析 |
| `skills/bio-*` | 15 个自定义 skill，串成 开工→出图→审计→报告→交付 流水线；并接 nature-* 发表链 |
| `commands/` | 自定义 slash 命令 |
| `agents/` | 自定义子代理：`bio-result-auditor`（只读审计）、`bio-report-writer`（出报告，固定 Opus 4.6） |
| `statusline-command.sh` | 状态栏脚本（git 分支 + 配额进度条） |
| `settings.local.json` | 权限白名单（Bash 命令 allow 规则） |
| `my-skills/habit-analyzer/` | 自定义 skill（使用习惯分析） |

## 外部依赖（不含在本库）

本环境还用到一个**第三方公开 skill 集**（非本人作品，按其许可使用，未复制进本库——请直接看上游）：

- **[Yuan1z0825/nature-skills](https://github.com/Yuan1z0825/nature-skills)** —— 投稿级科研写作/出图 skill 集，本人用到其中 9 个：
  `nature-figure`（R 后端出图）、`nature-writing`、`nature-polishing`、`nature-citation`、`nature-reader`、`nature-response`、`nature-data`、`nature-academic-search`、`nature-paper2ppt`。
- 本库的 `assets/figure-style/nature_theme.R` 即**基于 `nature-figure` 的 R 工作流扩展**（加了 CJK 安全字体、统一 house 样式与 ComplexHeatmap 热图模块）。

## 设计要点（建议重点看这些）

- **三层自动度**：全局原则（always-on）vs skill（触发才生效）vs 机械钩子，刻意把“轻原则”放全局、“重机器”按需加载。
- **质量闸**：交付前“数字台账”从源数据复算核验每个承重数字；docx/图表用确定性脚本校验（非肉眼）。
- **CJK 安全**：报告渲染与绘图字体自动解析中文可用字体，避免丢字/方块。
- **抗崩溃**：长审计/修复落盘 + 检查点，会话中断可续。
- **风格统一**：所有图 `source` 同一份 house 样式，一个交付一套风格。
- **按需绑模型**：报告生成委派给 `bio-report-writer` 子代理（frontmatter 钉死 Opus 4.6），主会话保持 Opus 4.8——per-subagent 模型独立。
- **交付↔发表打通**：bio-*（交付）与 nature-*（发表）靠 `report_claims + house图 + plan.md` 衔接；bio-grill/roundtable 已接文献检索（nature-academic-search）。

## 想请你评估

1. ①层（全局原则）和 ②层（skill）的边界划得合理吗？有没有该上移/下沉的？
2. 质量闸够不够？还是有过度工程的地方？
3. 还有哪些冗余、漏洞或单点风险？
4. 抗崩溃 / 溯源 / CJK 这几条的做法是否稳健？

## 说明

- 这是一份**忠实的自定义配置快照**：你亲手写/配的东西基本都在。**未含**外部共享 skill（如 nature-figure，软链到独立仓库）、Anthropic 插件自带 skill（docx/pptx 等），以及一切凭证与运行数据（凭证 / 会话 / 历史 / 客户数据）。
- skill 的 `*.md` 是给 Claude 的**工作流指令（prompt）**，不是可执行程序；`scripts/*.py` 才是确定性工具。
- 已脱敏，路径/名称为占位符，照搬前需按自己环境调整。
