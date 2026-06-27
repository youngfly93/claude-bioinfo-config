---
name: habit-analyzer
description: "分析 Claude Code 使用习惯，发现高频输入模式，推荐并创建 slash commands。当用户想要：(1)分析使用习惯 (2)查看高频输入 (3)总结工作流模式 (4)创建自定义命令 (5)优化工作流效率 时触发"
---

# 使用习惯分析器

分析 `~/.claude/history.jsonl` 中的历史记录，自动发现用户的使用模式，推荐并创建 slash commands。

## 分析流程

### Step 1: 高频输入统计

```bash
# 排除内置命令，统计高频输入
BUILTIN="^/(exit|clear|resume|init|compact|agents|model|status|mcp|login|plugin|help|rate-limit-options|config|doctor|memory|vim|undo|add-dir)"

cat ~/.claude/history.jsonl | jq -r '.display' | \
  grep -v -E "$BUILTIN" | \
  grep -v '^$' | \
  grep -v '^\`\`\`' | \
  grep -v '^---$' | \
  sort | uniq -c | sort -rn | head -30
```

### Step 2: 项目活跃度

```bash
cat ~/.claude/history.jsonl | jq -r '.project' | \
  sort | uniq -c | sort -rn | head -15
```

### Step 3: 模式自动发现

按输入长度分层分析：

```bash
# 短输入（<20字符）- 常用短命令/确认词
cat ~/.claude/history.jsonl | jq -r 'select((.display | length) > 0 and (.display | length) < 20) | .display' | sort | uniq -c | sort -rn | head -20

# 中等输入（20-100字符）- 常用指令模板
cat ~/.claude/history.jsonl | jq -r 'select((.display | length) >= 20 and (.display | length) < 100) | .display' | sort | uniq -c | sort -rn | head -20

# 长输入（>100字符）- 复杂工作流模板
cat ~/.claude/history.jsonl | jq -r 'select((.display | length) >= 100) | .display' | head -20
```

关键词聚类发现模式：

```bash
# 文件引用模式
cat ~/.claude/history.jsonl | jq -r '.display' | grep -E '@[a-zA-Z]' | sort | uniq -c | sort -rn | head -10

# 疑问句模式
cat ~/.claude/history.jsonl | jq -r '.display' | grep -E '\?|如何|怎样|什么|哪|吗' | sort | uniq -c | sort -rn | head -10

# 工具/技能调用模式
cat ~/.claude/history.jsonl | jq -r '.display' | grep -iE 'skill|配合|使用.*帮' | sort | uniq -c | sort -rn | head -10
```

### Step 4: 输出与推荐

呈现分析结果：

```
## 使用习惯分析报告

### 高频输入 Top N
| 频次 | 内容 | 建议命令名 |
|------|------|-----------|
| xx   | xxx  | /xxx      |

### 发现的模式
1. **模式名**: 描述（从数据聚类中发现）

### 项目活跃度
| 次数 | 项目路径 |
|------|----------|

### 推荐创建的命令
- `/xxx` - 内容: "..."
```

### Step 5: 创建命令

用户确认后创建：

```bash
# 检查已有命令避免重复
ls ~/.claude/commands/

# 创建新命令
echo '<内容>' > ~/.claude/commands/<命令名>.md

# 验证
cat ~/.claude/commands/<命令名>.md
```

## 推荐逻辑

适合做成命令的输入特征：
- 出现频次 >= 5
- 内容相对固定（非一次性长文本）
- 非纯代码块
- 非上下文强相关内容

命令名生成建议：
- 从内容提取核心动词/名词
- 保持简短（1-2个单词）
- 用户可自定义
