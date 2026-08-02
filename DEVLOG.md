# Dev Log — SkillForge

Running log of setup, gap-analysis runs, builds, and publishes.

## 2026-08-02 — Renamed job-hunter-agent → SkillForge

- Renamed the whole project (`job-hunter-agent/` → `skillforge/`) since the current scope is
  purely resume-gap-analysis → portfolio-project generation, not job discovery/application yet —
  "job hunter" overstated what it does today. All internal references (CLAUDE.md, agent defs,
  dashboard, README) updated to match. Job discovery/auto-apply remains a planned future module;
  the name can expand again once that's built.

## 2026-08-02 — Setup

- Project scaffolded at `skillforge/`, sibling to `multi-agent-builder/`.
- Reused `planner`, `coder`, `reviewer` agents as-is from `multi-agent-builder`.
- Added `gap-analyzer` agent: compares resume vs. target roles (Data Scientist / Data Engineer /
  AI Engineer, Sweden/EU, ~2-3yr level), checks against existing GitHub (github.com/rapidvind)
  and resume to avoid proposing duplicate projects, proposes ranked buildable projects.
- Added `publisher` agent: git init/commit + `gh repo create` push + devlog entry; falls back to
  manual steps if `gh` CLI isn't installed/authenticated (not present on this machine yet).
- Resume copied to `data/resume/Aravind_Dora_Resume_2026_ATS.pdf`; target roles defined in
  `data/targets/target_roles.md`.
- Scope decision: MVP is gap-analysis → build → publish, with explicit approval gates before
  build and before publish (separate asks). Job discovery/auto-apply deferred as a future
  pluggable module — avoids job-board ToS/bot-detection risk until scoped separately.
- Next: run first real gap-analysis pass; build a pipeline-status visualizer.

## 2026-08-02 — Live Dashboard

- Added Forward Deployed Engineer to `data/targets/target_roles.md` as a 4th target role family.
- Replaced the initial static claude.ai Artifact visualizer with a **local live dashboard**
  (`dashboard/index.html` + `dashboard/server.py`, Python stdlib only) — Artifacts can't reach
  local files or push live updates in this session (only `downloads`/`mcp` runtime capabilities
  available, no generic shared-state capability), so a small local server was the correct fit
  instead.
- Dashboard polls `state/pipeline.json`, `state/gaps.json`, `state/projects.json` every 2.5s.
- Made it interactive: Approve build / Approve publish / Skip / Cancel buttons, plus a free-text
  "send a note" box — all POST to `/api/approve`, queued in `state/approvals.json` for the
  orchestrator to pick up at the start of its next turn (this session isn't a running daemon, so
  clicks queue rather than trigger instantly).
- Added an Issues banner: any pipeline stage marked `blocked` (agent error, needs input) surfaces
  with Retry/Cancel buttons rather than silently stalling.
- Updated `CLAUDE.md`: orchestrator now checks `state/approvals.json` first every turn, writes
  `pipeline.json`/`gaps.json`/`projects.json` at every step, and added a Token Efficiency section
  (don't restate full state in chat once the dashboard is live, don't re-read/re-fetch things
  already known this session).
- Verified end-to-end via smoke test: server starts, static files serve, `/api/approve` writes
  correctly for gap/project/stage/general note kinds.
- Known limitation: the server only runs as long as this Claude Code session's background task
  is alive — needs a manual restart (`python dashboard/server.py`) after a session ends.

## Build Runs

### 2026-08-02 — Round 1: RAG Eval & Observability Platform

- **Gap analysis**: ran `gap-analyzer` inline (this session's cwd is `multi-agent-builder`, so the
  skillforge custom agent types aren't registered here — see note below). Researched real,
  live Stockholm postings via the Indeed MCP connector (five companies across retail tech,
  fintech, and consulting) rather than relying on generic/stale knowledge. Found 5 ranked gaps —
  full detail kept locally, not published (real employer names):
  1. Production LLM systems (RAG/eval/observability) — seen in an AI Engineer posting
  2. Analytics engineering (dbt) — seen in two postings
  3. Streaming pipelines (Kafka) — seen in a posting
  4. Azure cloud — seen in a consulting-firm posting
  5. Production software rigor (testing/CI-CD/APIs) — closest transferable skill to Forward
     Deployed Engineer, since no direct FDE postings turned up in Sweden
  - Also flagged Swedish language proficiency as a real, recurring requirement that isn't
    project-closeable, so it was noted rather than turned into a fake project.
- **Approval**: user approved Gap 1 (Production LLM systems) via the dashboard's Approve-build
  button, queued in `state/approvals.json` and picked up at the start of the next turn.
- **Planning**: `planner` agent produced a spec for **RAG Eval & Observability Platform** — a
  locally-runnable RAG assistant over a synthetic medical-report corpus (avoids real-PII/licensing
  issues while echoing the existing "Safe Scraper" domain), with a retrieval+hallucination eval
  suite (CI-runnable via pytest/GitHub Actions) and a Streamlit observability dashboard (latency,
  token cost, hit-rate). Scoped to run with no paid infra required (local Chroma + sentence-
  transformers; OpenAI generation is optional with a retrieval-only fallback if no API key is set).
- **Coding**: `coder` agent dispatched to write the project to
  `output/rag-eval-observability-platform/` — in progress as of this entry; its own detailed
  build log lands in that project's own `DEVLOG.md` per the spec.
- **Note on agent discovery**: this whole round was driven from a Claude Code session whose
  working directory is `multi-agent-builder/`, not `skillforge/` — custom agent types
  (`gap-analyzer`, `publisher`) aren't discoverable from there, so gap-analysis was run inline
  following the same `gap-analyzer.md` instructions rather than as an isolated subagent. Running
  `claude` from inside `skillforge/` directly would let all 5 custom agents load normally.

<!-- Next entry goes here -->
