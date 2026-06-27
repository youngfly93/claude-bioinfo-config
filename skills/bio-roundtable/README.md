# bio-roundtable

A Claude Code skill that runs structured roundtable discussions on bioinformatics analysis results — generating non-trivial hypotheses, new analytical angles, and validation plans.

## Installation

Copy the `SKILL.md` file into your Claude Code skills directory:

```bash
# Create the skill directory
mkdir -p ~/.claude/skills/bio-roundtable

# Clone and copy
git clone https://github.com/youngfly93/bio-roundtable.git
cp bio-roundtable/SKILL.md ~/.claude/skills/bio-roundtable/
```

Or directly:

```bash
mkdir -p ~/.claude/skills/bio-roundtable
curl -o ~/.claude/skills/bio-roundtable/SKILL.md \
  https://raw.githubusercontent.com/youngfly93/bio-roundtable/main/SKILL.md
```

## Usage

In Claude Code, invoke the skill with:

```
/bio-roundtable <your question or context>
```

### Two Modes

| Mode | When to use | Trigger phrases |
|------|-------------|-----------------|
| **insight** (default) | You have results but need fresh hypotheses, stronger mechanistic stories, or new analytical angles | "还有什么新角度", "故事怎么讲更强", "roundtable", "圆桌讨论", "新见解" |
| **validation** | You have candidate hypotheses and need discriminative validation plans | "下一步怎么验证", "做什么实验", "怎么确认", "验证设计" |

### Examples

**Insight mode** — find new angles for existing DEG results:

```
/bio-roundtable 我的转录组差异分析发现了200个DEGs，富集到EMT和免疫浸润通路，
但reviewer说故事太常规了，有没有更强的切入角度？
```

**Validation mode** — design experiments to confirm a hypothesis:

```
/bio-roundtable validation 我们发现GIST中KIT突变型和野生型的免疫微环境完全不同，
假说是KIT信号通过STING通路调控PD-L1表达，下一步怎么验证？
```

**Evaluate project feasibility:**

```
/bio-roundtable 请评估这个课题方向是否有足够的现实意义，能否发表一篇文章
```

### What it does

1. **Receives the topic** — extracts your background, existing results, current interpretation, and resource constraints
2. **Lays out facts** — the moderator objectively states key findings, contradictions, and ignored signals (no interpretation)
3. **Competing hypotheses** — multiple roles propose 2-5 high-discrimination hypotheses with evidence and weaknesses
4. **Conflict focus** — roles debate the deepest disagreement, not superficial consensus
5. **Structured output** — delivers actionable insights or validation plans in tabular format

### Roles

**Fixed core** (always present):
- **Moderator** — lays facts, compresses conflicts, takes no position
- **Mechanism Builder** — chains molecules/pathways/phenotypes into testable causal links
- **Contrarian** — finds alternative hypotheses and counter-evidence
- **Experiment Designer** — designs minimal-cost validation paths

**Flexible seats** (1-2 per topic):
- Anomaly Hunter, Statistics Reviewer, Methods Hacker, Translational Advisor, Resource Manager

### Not suitable for

- Pure execution tasks (just run a pipeline)
- Data quality not yet confirmed
- Standard delivery reports only
- Already know exactly what to validate

## License

MIT
