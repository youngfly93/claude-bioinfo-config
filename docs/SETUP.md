# SETUP · 在新机器上配置这套生信交付 harness（含 Windows）

> 适用：把本仓库（`claude-bioinfo-config` / 插件 `bio-delivery`）配到一台新机器。
> **可直接交给那台机器上的 Claude Code**：说「按 `docs/SETUP.md` 帮我配置这台机器」，让它照步骤走、最后跑「验证」。

## 先懂一件事：能力 ≠ 政策（否则你会"装了 skill 却不生效"）

| 层 | 是什么 | 随插件走吗 |
|---|---|---|
| **能力** | bio-* skills、hooks、harness 引擎、house 样式、agents | ✅ `/plugin install` 就有 |
| **政策** | CLAUDE.md 里的规则（出图用 R、科研严谨、文档卫生、工作区操作约定） | ❌ **每台机器手写**，插件不会替你装 |

**典型坑**：装了 `nature-figure` skill，但它**设计上绝不自己默认 R**——它会问 "Python or R?" 然后停。让它"默认走 R"的是 CLAUDE.md 里那条规则。**规则没到位 → skill 装了也不走 R。**

### CLAUDE.md 加载层级（决定政策在哪生效）

```
① 全局    ~/.claude/CLAUDE.md            每个会话都加载（always-on）
② 工作区  <你的生信工作根>/CLAUDE.md     cwd 在这棵树下才加载
③ 项目    <分析项目>/CLAUDE.md           cwd 在该项目才加载
（插件仓库自带的 CLAUDE.md 不算政策——只在你 cd 进仓库时读，分析时不加载）
```

做分析时你的 cwd 在分析项目里 → 真正生效的是 **①+②+③**。所以**政策必须落进 ① 全局或 ② 工作区**，光装插件没用。

## 安装步骤

### 1. 装插件（拿到能力）
```
/plugin marketplace add youngfly93/claude-bioinfo-config
/plugin install bio-delivery@youngfly93-bioinfo
```

### 2. 装本仓库不含的外部依赖
- **nature-skills**（出图/写作 skill，**不在本仓库**，见 README「外部依赖」）：
  ```
  git clone https://github.com/Yuan1z0825/nature-skills
  ```
  把它的 `skills/*` **复制**进 `~/.claude/skills/`。**Windows 用复制，别用软链**（Windows 软链要开发者模式且易断）。
- **R 环境**：装 R + 确保 `Rscript` 在 PATH；装包 `ggplot2`、`patchwork`、`ComplexHeatmap` 等；配 **CJK 字体**（Windows 用「微软雅黑」/「宋体」，不是 Mac 的字体名）。
- **Python 依赖**：`python-docx`（docx_check 用）等。

### 3. 落政策层（关键！插件不会替你做）
- **全局 ①**：把本仓库根的 `CLAUDE.md` 复制到 `~/.claude/CLAUDE.md`（Windows：`%USERPROFILE%\.claude\CLAUDE.md`）。→ 拿到绘图规则 + 科研严谨 + 文档卫生。
- **工作区 ②**：把 `docs/workspace.CLAUDE.example.md` 复制到**你生信工作根目录**的 `CLAUDE.md`，填里面的 `<占位符>`（服务器名、传输方式、目录结构、已有流程）。

### 4. 修路径假设
house 样式那条 `source("~/.claude/assets/figure-style/nature_theme.R")`——确认这个路径在本机真存在（插件可能装在别处）。Windows 下 `~` 在 R 里解析可能不同；必要时改成实际绝对路径，或用 `${CLAUDE_PLUGIN_ROOT}` 解析。

## 验证（配完逐条跑）
- [ ] `Rscript --version` → R 在 PATH。
- [ ] `~/.claude/skills/` 里有 `nature-figure`，且能打开 SKILL.md（不是断链）。
- [ ] `~/.claude/CLAUDE.md` 里有「## 绘图」段（出现 `nature-figure` / `直接选 R` / `Python 不画图`）。
- [ ] 让它"画个测试图" → 应路由到 nature-figure → **按规则直接走 R**（而不是 Python，也不是卡在问 Python/R）。
- [ ] harness 预检：`bash <harness>/specs/preflight_check.sh .`（Windows 用 Git Bash 或 WSL 跑 `.sh`）。

## Windows 专属注意
- **软链不可靠** → nature-skills 等一律**复制**，别 symlink。
- **路径 / `~`** → 脚本里的 `~/.claude/...` 在 Windows 可能不解析；R 的 `source()` 尤其要确认实际路径。
- **CJK 字体** → 用 Windows 自带中文字体名，别套 Mac 字体。
- **bash 脚本** → harness 是 sh/python；Windows 用 **Git Bash 或 WSL** 跑 `.sh`，纯 PowerShell 跑不了。
