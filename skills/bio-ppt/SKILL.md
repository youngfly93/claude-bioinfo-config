---
name: bio-ppt
description: 生信汇报/组会/journal club/paper 分享/答辩/pitch 的极简双语(中英) .pptx 生成器，走数据可视化艺术家 Shirley Wu(sxywu)的极简美学——大留白、一页一意、标志红(#cc0000)、灰阶字层级、Quicksand/Playfair/Atkinson + 中文黑体、章节侧标、页脚签名、白底或深灰(#222)底；含拉丁字体嵌入(跨平台不变形)、双图对比版式、演讲备注、内容 lint。工作流强制"故事板先行"(总-分-总)。Use when the user wants bio/生信 presentation slides, 组会/journal club/paper 分享/答辩/pitch decks, a "Shirley Wu 风格 / sxywu 风格" 或极简双语 PPT, or references this skill (bio-ppt) by name. 与 bio-report(Word 报告)成对：report=Word、ppt=PPT。NOT for formal SCI figure decks or 正式客户书面交付(用规范模板)。
---

# bio-ppt · 生信极简汇报 PPT（Shirley Wu 风格）

产出**中英双语、极简、无涂鸦**的 .pptx，复刻数据可视化艺术家 Shirley Wu 的招牌美学（大留白、一抹标志红、清晰字层级、章节侧标）。`bio-` 系列里与 `bio-report`(Word) 成对：report=Word、ppt=PPT。

## 工作流

> ⛔ **硬门槛**：故事板(Phase 0)未经用户确认，**不要写 content.json**。极简 deck 的成败 80% 在结构，不在排版。

### 0. 故事板对齐（动手前必做）
按 [references/storyboard.md](references/storyboard.md) 走「总-分-总」：
定受众 + 一句话结论 → 搭骨架 → 逐节定 message / 选图 / 版式 → 站客户角度顺一遍 → **用户点头**。
**分工**：用户选/确认分析包路径、拍板哪张是关键图、做客户视角终审；本 skill 负责组织故事线、提候选图、起草故事板与自查。关键图「我提议、用户拍板」。

### 1. 读设计原则
阅读 [references/style.md](references/style.md) —— 七条铁律 + 叙事骨架。**这决定内容"像不像她"**，比模板本身更重要。

### 2. 把内容写成 content.json
按 [references/content-spec.md](references/content-spec.md) 的 schema 组织。10 种版式：
`cover · section · statement · content · two_column · list · table · photo · photo_pair · closing`。

授权内容时严守纪律：**一页一个意思、标题≤6词、正文≤3句、留白优先**。和用户对齐主题与叙事弧线后再写，别擅自堆料。
**极简 deck 务必给每页写 `notes`（演讲备注）**——页面越空越靠口头讲。图片可借 `meta.base_image_dir` 用相对路径。

### 3. 生成
```bash
python3 scripts/build_deck.py <content.json> <output.pptx>
```
- **拉丁字体自动嵌入 pptx**（`meta.embed_fonts` 默认 true）→ 换电脑 / 发 Windows / 发客户都不变形。
- 首次还会把字体装到 `~/Library/Fonts` 供本机 LibreOffice 预览。
- 生成时会打印**内容 lint 警告**（标题过长 / 正文过多行），据此精简。
- 中文 `PingFang SC` 无法嵌入：Mac 自带，Windows 回退系统中文字体。跨平台一致见 content-spec.md「跨平台」。

### 4. 验证（推荐）
```bash
bash scripts/preview.sh <output.pptx>        # 一条命令出逐页预览 PNG（需 LibreOffice）
```
检查：是否有页面过满、标志红是否被滥用、侧标/页脚是否到位、中英字体是否各就各位。
⚠️ 仅 LibreOffice 验证 ≠ 真 PowerPoint；字体嵌入主要保障真 PowerPoint/Keynote 场景，条件允许时在目标软件复核一次。

## 设计 token（速记，改风格去 scripts/build_deck.py 顶部常量）
- 标志红 `#cc0000`（仅重点）｜主文字 `#222`｜次级 `#696969`｜注释 `#888`｜虚化 `#ccc`
- 英文标题 Quicksand（大写+大字距）/ Playfair Display（衬线情绪）｜英文正文 Atkinson Hyperlegible｜中文 PingFang SC
- 16:9，白底或深灰 `#222` 底

## 边界
- 走她"极简专业"的一面：**不含手绘涂鸦/彩铅/D3 交互**（那些需人手或网页，程序生成不了）。
- 适用：组会、paper 分享、pitch、学术报告、个人演讲。
- **不适用**：正式 SCI 图表稿、临床报告、客户交付——那些仍用既有规范模板，别套此风格。

## 资源
- `scripts/build_deck.py` —— 生成器（版式/配色/双语字体/字体嵌入/lint/自动安装，集中改这里调风格）
- `scripts/preview.sh` —— 一条命令渲染逐页预览 PNG
- `assets/fonts/` —— 自带开源静态字体（Quicksand / Playfair Display / Atkinson Hyperlegible，Regular/Bold/Italic）
- `assets/example_content.json` —— 生信场景的完整示例（可直接套改）
- `references/style.md` · `references/content-spec.md`
