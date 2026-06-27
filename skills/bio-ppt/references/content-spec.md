# 内容规格（content.json）

`build_deck.py` 读取一个 JSON：顶层 `meta` + `slides` 数组。每个 slide 的 `type` 决定版式。
**核心纪律：一页一个意思、字越少越好、大留白。** 宁可多分几页，不要把一页塞满。

## meta
```json
"meta": {
  "handle": "@yourhandle",        // 页脚签名左半，可省
  "site":   "yoursite.com",       // 页脚签名右半，可省
  "cjk_font": "PingFang SC",      // 中文字体；想更接近她的几何感可填 "Source Han Sans SC"（需自行安装）
  "embed_fonts": true,            // 默认 true：把拉丁字体嵌入 pptx，换电脑/发 Windows 也不变形
  "base_image_dir": "/abs/dir"    // 可省；填了之后各页 image 可写相对路径，免去重复粘贴长绝对路径
}
```
> **跨平台**：拉丁字体(Quicksand/Playfair/Atkinson)会嵌入 pptx，任何机器打开都正确。
> **中文** PingFang SC 体积大、无法嵌入：Mac 自带；Windows 会回退到系统中文字体(微软雅黑/黑体)。
> 要 Windows 也完全一致，把 `cjk_font` 设为对方装了的字体(如 "Source Han Sans SC" 思源黑体)。

## 通用可选字段（多数版式都支持）
- `dark`: true → 深灰 #222 底白字（章节/金句/情绪页常用）。
- `side_label`: 左缘竖排小字，如 `"01. question"`（她的招牌导航母题；编号+主题）。
- `notes`: 该页演讲备注，写入 PPT 备注页。**极简 deck 强烈建议每页都写**——页面越空，越靠口头讲。
- 页脚签名自动从 meta 注入，无需每页写。

## 10 种版式

### cover 封面
```json
{"type":"cover","title_en":"Single-Cell Atlas","title_zh":"单细胞图谱分析",
 "subtitle":"一句副标题","author":"杨非 · 2026","serif":true,"dark":false}
```
`serif:true` → 英文标题用 Playfair Display 衬线（情绪感）；`false` → Quicksand 几何无衬线。

### section 章节分隔（默认深底）
```json
{"type":"section","number":"01","title_en":"the question","title_zh":"我们在回答什么","dark":true}
```
`number` 显示为标志红大号编号。

### statement 金句 / 单句陈述
```json
{"type":"statement","text_zh":"数据不是终点，故事才是。",
 "text_en":"data is not the destination — the story is.","dark":false,"side_label":"04. takeaway"}
```
中文为主句（大号），英文为 Playfair 斜体辅句（可省）。整页极致留白。

### content 单点内容
```json
{"type":"content","title_en":"WORKFLOW","title_zh":"分析流程",
 "title_center":false,"body":["第一行","第二行","..."],"body_size":20,"side_label":"02. method"}
```
`body` 是字符串数组，每项一段，居中偏中部。英文标题自动 Quicksand 大写+大字距。

### two_column 双栏对比
```json
{"type":"two_column","title":"DATA SOURCES 数据来源",
 "left":{"head":"自产数据 in-house","items":["A","B","C"]},
 "right":{"head":"公共数据 public","items":["X","Y","Z"],"muted":true},
 "side_label":"02. method"}
```
`muted:true` 把该栏整体灰化（她常用来弱化"非重点"那一栏）。

### table 极简表格（Table-1 / 指标汇总）
```json
{"type":"table","title_en":"COHORT","title_zh":"队列基线 (n=1688)",
 "headers":["变量","对照 (n=832)","病例 (n=856)","P"],
 "rows":[["年龄","58.5 (12.2)","59.0 (12.9)","0.43"],
         ["FPG","5.64 (1.43)","8.07 (3.12)","<0.001"]],
 "side_label":"02. method"}
```
极简风：表头标志红下划线、行间淡分隔线、**无竖线无填充**。首列左对齐(主色)，其余居中(灰)。
用于**队列特征表(Table-1)、模型指标汇总表**。`table_width` 可调(默认 10.4in)。
- 数字必须**溯源真实结果文件**(如 `Table_1_baseline.csv`、Phase4 `mice_model_auc_summary.csv`)，绝不杜撰。
- 建议 ≤ 7 行 × ≤ 5 列；表注/显著性说明放该页 `notes`。

### list 列表（编号或圆点）
```json
{"type":"list","title_en":"KEY FINDINGS","title_zh":"核心发现",
 "numbered":true,"items":["发现一","发现二","发现三"],"side_label":"03. results"}
```
序号/圆点用标志红。建议每页 ≤ 5 条。

### photo 单图
```json
{"type":"photo","image":"path/fig.png","caption":"图注（可省）",
 "dark":false,"fit":"wide","side_label":"00. data"}
```
图片**等比例**缩放居中（contain，不拉伸）。缺图会显示红色占位提示。
- `image`：绝对路径，或相对 `meta.base_image_dir` 的相对路径。
- `fit:"wide"`：宽图(如 Manhattan、列线图，宽高比 ≥2:1)用更宽的框，避免被缩太小。
- **白底科研图表(ROC/森林图/热图)建议 `dark:false`**（图本身白底，与白底页融为一体最干净）。

### photo_pair 双图并排
```json
{"type":"photo_pair","title":"TRAIN vs TEST 训练/测试",
 "images":["a.png","b.png"],"captions":["训练集","测试集"],
 "dark":false,"side_label":"03. results"}
```
两图左右并排，用于 ROC train/test、校准 vs DCA 等对比。`captions` 可省/部分省。

### closing 结尾
```json
{"type":"closing","title_en":"thank you","title_zh":"谢谢","links":["@yourhandle","yourlab.studio"]}
```

## 颜色/字体速记（改风格去 scripts/build_deck.py 顶部）
- 标志红 `#cc0000`（仅重点）｜主文字 `#222`｜次级 `#696969`｜注释 `#888`｜虚化 `#ccc`
- 英文标题 Quicksand / Playfair Display｜英文正文 Atkinson Hyperlegible｜中文 PingFang SC
