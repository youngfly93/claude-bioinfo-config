# bio-grill

A Claude Code skill that grills you on your analysis design **before** you run it — aligning sample/grouping/contrast/batch/filtering/normalization/model/threshold one question at a time, each with a recommended answer, then producing an "analysis design sign-off sheet" you approve before the pipeline runs.

It directly targets the #1 bioinformatics failure mode: *the agent ran an analysis you didn't quite mean*.

## Usage

In Claude Code:

```
/bio-grill
帮我盘一下这个 RNA-seq 差异分析怎么设计
```

Or just say "审问我" / "开工前对齐" / "分析前检查" before starting an analysis.

### Two intensity modes

| Mode | When to use | Behavior |
|------|-------------|----------|
| **探索（default）** | Quick look at a trend | Asks only the 4 core questions (grouping/pairing · contrast direction · batch · key thresholds), recommends defaults for the rest |
| **高风险 / 交付 / 临床相关** | Delivery-grade, clinical-facing reports, anything facing reviewers/clients | Grills every axis in `CHECKLIST.md`, each requires your confirmation |

It states which mode it's in up front; if unsure it asks.

### Files

- `SKILL.md` — modes, grilling discipline, flow, sign-off sheet
- `CHECKLIST.md` — full per-data-type grilling axes (RNA-seq / proteomics-DIA-PTM / single-cell / 16S-metagenomics)
- `DECISION-FORMAT.md` — when & how to record "why this analysis" decisions into `docs/analysis-decisions/`

### How it relates to your other skills

| Stage | Skill |
|-------|-------|
| **Before** analysis — align the design | **bio-grill** |
| After analysis — generate new insight / validation plans | `bio-roundtable` |
| Package & deliver | `bio-deliver` |
| Session handoff | `save` / `now` |
| Environment check | `preflight` |

### Three-layer documentation split (used by `DECISION-FORMAT.md`)

- `CONTEXT.md` — terminology, sample naming, contrast meanings
- `plan.md` — analysis steps & progress
- `docs/analysis-decisions/` — *why* a given analytical choice was made (recorded sparingly)

### Not suitable for

- Pure execution of an already-confirmed analysis
- Interpreting results / generating hypotheses (use `bio-roundtable`)
- Delivery packaging (use `bio-deliver`)
