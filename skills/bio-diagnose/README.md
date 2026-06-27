# bio-diagnose

A Claude Code skill that brings **debugging discipline** to bioinformatics: when an analysis won't run, gives weird results, can't be reproduced, or got slow.

Core principle (adapted from disciplined-diagnosis practice): **build a fast, deterministic, agent-runnable pass/fail feedback loop first — then the bug is 90% solved.** Everything else (minimise → hypothesise → instrument → fix → regression-test) just consumes that signal.

## Usage

In Claude Code, when something breaks:

```
/bio-diagnose 我的 DESeq2 结果 logFC 符号好像全反了
```

Or just describe a bug / weird result / "跑不通" / "数字对不上" / "为什么这么慢" — it triggers automatically.

## Files

- `SKILL.md` — the six-phase discipline (reproduce → minimise → hypothesise → instrument → fix → regression-test), feedback-loop first
- `LOOPS.md` — how to build bioinformatics feedback loops, with R/Python/Nextflow/Snakemake snippets (mini fixtures, intermediate-table snapshots, old↔new diff, invariant assertions, git bisect, profiling)
- `PITFALLS.md` — high-frequency bioinformatics root causes (sample misalignment, ID mapping, reference-level direction, NA propagation, batch confounding, env drift, unset seed, count-vs-TPM, OOM…)

## How it relates to your other skills

| Stage | Skill |
|-------|-------|
| Before analysis — align the design | `bio-grill` |
| **During — when it breaks / looks wrong / is slow** | **bio-diagnose** |
| After — generate new insight / validation plans | `bio-roundtable` |
| Audit results vs plan.md | `/check`（bio plugin command） |
| Environment precheck | `preflight` |

Together `bio-grill → bio-diagnose → bio-roundtable` cover before / during / after of an analysis.

## Not suitable for

- Pre-analysis design alignment (use `bio-grill`)
- Results are correct but you want new interpretation/hypotheses (use `bio-roundtable`)
- Plain environment precheck (use `preflight`)
