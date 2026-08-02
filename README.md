# SkillForge

A multi-agent pipeline that turns resume gaps into real, published portfolio projects —
built to reduce the manual time spent job-hunting and upskilling.

## Architecture

```
You
 └── Orchestrator (CLAUDE.md)
       ├── gap-analyzer agent  →  resume + target roles → ranked gaps + project ideas
       │                          (you approve which gap to build)
       ├── planner agent       →  approved idea → structured spec
       ├── coder agent         →  spec → working code (output/<slug>/)
       ├── reviewer agent      →  code → review
       │                          (you approve publishing)
       └── publisher agent     →  git init/commit → GitHub repo + devlog entry
```

## How to Run

```bash
cd skillforge
claude
```

Then just say "run a gap analysis" (or similar) to kick off Step 1. The orchestrator will stop
and wait for your go-ahead before building anything, and again before publishing anything.

## Project Structure

```
skillforge/
├── CLAUDE.md                  # Orchestrator
├── .claude/agents/
│   ├── gap-analyzer.md
│   ├── planner.md
│   ├── coder.md
│   ├── reviewer.md
│   └── publisher.md
├── data/
│   ├── resume/                # Your resume (source of truth for gap analysis)
│   └── targets/target_roles.md
├── state/
│   ├── gaps.md                 # Ranked gaps + status
│   └── projects.md             # Build/publish status per project
├── output/                    # Built projects land here, one folder each
└── DEVLOG.md                  # Detailed log of every build + publish run
```

## Status

MVP scope: gap analysis → project generation → build → publish, all with explicit approval
gates. Job discovery/auto-apply is a planned future module (kept separate since it depends on
external job-board access and carries its own ToS/automation risk that needs its own scoping).

## Requirements

- GitHub CLI (`gh`), authenticated (`gh auth login`) — needed for the publisher agent to
  create repos automatically. Without it, publisher falls back to printing manual steps.
