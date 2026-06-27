# bio-zoom-out

A small Claude Code skill that **zooms out** and draws a map of an unfamiliar bioinformatics sub-project: what biological question it answers, how data flows through the numbered scripts, where the key files are, what stack it runs on, and how far along it is.

Adapted from a generic "zoom out for a higher-level view" pattern, tailored to this workspace's shape (numbered-script pipelines, `plan.md`-driven progress, `data/`/`results/`, local vs server `<compute-server>`).

## Usage

```
/bio-zoom-out
```

Or just say "梳理一下这个项目" / "这个目录是干嘛的" / "我不熟这个项目" / "给我画张地图" when you land in a sub-project you don't know (a collaborator's directory, or your own from months ago).

## What it does

Read-only. Reads `plan.md` → `CONTEXT.md`/`README` → `CLAUDE.md`/`AGENTS.md` → `scripts/` (numbered order) → `data`/`results`/`config`, then outputs a scannable map:

1. One-line positioning — biological question, owner, stage
2. Analysis pipeline — data flow step by step in script order
3. Key file locations
4. Stack & runtime (R/Python/Nextflow/Shiny; local vs server)
5. Current progress from `plan.md`

It does not run analyses or modify files, reuses existing docs rather than duplicating them, and flags anything it had to infer or that looks off.

## How it relates to your other skills

| Need | Skill |
|------|-------|
| **Understand an unfamiliar sub-project** | **bio-zoom-out** |
| Align an analysis design before running | `bio-grill` |
| Debug when something breaks / looks wrong | `bio-diagnose` |
| Generate new insight from results | `bio-roundtable` |

## Not suitable for

- You already know the project and just want to run a step (just do it)
- Debugging a specific bug (use `bio-diagnose`)
