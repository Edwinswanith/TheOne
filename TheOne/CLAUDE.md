# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**GTMGraph** — an evidence-backed go-to-market planner that turns a product idea into a decision-complete, evidence-linked execution plan across 4 business pillars, rendered as a grouped graph with accountable overrides.

**Repository:** https://github.com/Edwinswanith/TheOne.git

## Commands

### Setup
```bash
docker compose up -d          # Start Postgres + Redis
uv sync --all-groups          # Install Python deps
pnpm install                  # Install JS deps
make migrate                  # Run Alembic migrations
```

### Development
```bash
make api                      # FastAPI server (uvicorn --reload on :8000)
make worker                   # Celery worker for async runs
pnpm web:dev                  # Next.js dev server
```

### Testing
```bash
make test                     # All Python tests (pytest -q)
uv run pytest services/orchestrator/tests/test_merge_rules.py -q   # Single test file
uv run pytest -k "test_name" -q                                    # Single test by name
pnpm web:lint                 # Frontend lint
pnpm web:build                # Frontend build check
```

### Database
```bash
make migrate                              # Apply migrations
make migration m="describe_change"        # Create new migration
```

## Architecture

### Monorepo Layout
- `apps/web/` — Next.js (TypeScript), React Flow graph, Zustand state, Tailwind CSS
- `services/api/` — FastAPI HTTP API + SSE streaming (`services/api/app/main.py` is the single router)
- `services/orchestrator/` — Core business logic: agents, merge engine, validator, runtime pipeline
- `services/worker/` — Celery tasks for async run execution
- `services/export/` — Markdown + HTML export renderer
- `packages/shared/schemas/` — JSON Schemas (`canonical_state.schema.json`, `agent_output.schema.json`)
- `Root/` — Product specs (PRD, schemas, validator rules) — source of truth for requirements
- `test/` — Product acceptance test cases (TC-001 to TC-020)

### Provider System (Fixture vs Real)
Controlled by `GTMGRAPH_USE_REAL_PROVIDERS` env var in `services/orchestrator/tools/providers.py`:
- **Fixture mode** (default, `false`): Reads deterministic JSON from `services/orchestrator/fixtures/`. Used in tests and CI.
- **Real mode** (`true`): Calls Perplexity API (`sonar-pro` model) for evidence retrieval and Gemini API (`gemini-2.0-flash`) for synthesis. Requires `perplexity_api_key` and `Google_API_Key` in `.env`.

### Canonical State
Single source of truth JSON object flowing through the system. Schema: `packages/shared/schemas/canonical_state.schema.json`. Top-level keys: `meta`, `idea`, `constraints`, `inputs`, `evidence`, `decisions`, `pillars`, `graph`, `risks`, `execution`, `telemetry`. Every state mutation is validated via `services/orchestrator/state/validation.py` and snapshotted.

### Pipeline Runtime (`services/orchestrator/runtime.py`)
Runs 12 agents sequentially per `AGENT_SEQUENCE` in `services/orchestrator/dependencies.py`:
`evidence_collector → icp_agent → positioning_agent → pricing_agent → channel_strategy_agent → sales_motion_agent → product_strategy_agent → tech_architecture_agent → people_cash_agent → execution_agent → graph_builder → validator_agent`

Each agent produces an `AgentOutput` (structured diffs with patches, proposals, facts, assumptions, risks). The merge engine (`services/orchestrator/state/merge.py`) applies outputs deterministically.

### Merge Rules (Critical — read `merge.py` before modifying)
- **Decision ownership:** Only orchestrator can write `decisions.*.selected_option_id` — agents submit proposals only
- **Patch ordering:** Evidence → Decisions → Pillars → Graph → Execution → Telemetry
- **Evidence dedup:** Merge by normalized URL, keep max quality score (`services/orchestrator/tools/evidence.py`)
- **Conflict resolution:** Evidence > Inference > Assumption; two evidence sources on same path → create candidates + validator contradiction
- **Node ID stability:** Stable IDs like `market.icp.summary` — upsert by ID, never duplicate
- **Source-less claims:** Evidence patches without sources auto-downgrade to assumption (confidence capped at 0.6)

### Dependency DAG (`services/orchestrator/dependencies.py`)
`DECISION_DEPENDENCY_GRAPH` maps which decisions cascade: changing ICP reruns pricing, channels, sales_motion, positioning. `DECISION_TO_AGENTS` maps decisions to the agents that must re-execute. `ALWAYS_RUN_AGENTS = {graph_builder, validator_agent}`.

### Validator (`services/orchestrator/validators/rules.py`)
14 rules from the conflict matrix (V-ICP-01 through V-CONT-01). Critical/high severity rules block completion/export. Validator writes to `state.risks.contradictions[]`.

### SSE Streaming
API endpoint `GET /runs/{run_id}/stream` returns `text/event-stream`. Events: `run_started`, `agent_started`, `agent_progress`, `agent_completed`, `state_checkpointed`, `node_updated`, `run_completed`, `run_failed`, `run_blocked`. Frontend subscribes via `apps/web/src/lib/sse.ts`.

### API Store
`services/api/app/store.py` provides `MemoryStore` (in-memory) with `db_models.py` defining SQLAlchemy models for Postgres persistence. State snapshots are versioned per run for diffing and rollback.

## Key Design Constraints
- Graph nodes use stable IDs (e.g., `market.icp.summary`) — never random UUIDs for domain nodes
- Every claim must be evidence-backed or labeled assumption with confidence 0.0–1.0
- Overrides require justification text and generate stored impact warnings with dependency cascade
- Partial reruns recompute only dependent agents (not the full pipeline)
- 4-pillar model: **Market to Money**, **Product**, **Execution**, **People and Cash**

## Environment Variables (`.env`)
```
Google_API_Key=              # Gemini API
perplexity_api_key=          # Perplexity API
DATABASE_URL=postgresql+psycopg://gtm:gtm@localhost:5432/gtmgraph
REDIS_URL=redis://localhost:6379/0
GTMGRAPH_USE_REAL_PROVIDERS=false
GTMGRAPH_PROVIDER_FIXTURE_ROOT=services/orchestrator/fixtures
```

## CI
GitHub Actions (`.github/workflows/ci.yml`): Python 3.12, uv, `pytest -q` on push to main and PRs.

## Design System
- **Theme:** Pencil sketch — warm off-white background, charcoal foreground, muted sage accent, muted amber for warnings
- **Typography:** Inter (body/UI), Source Serif 4 (headings)
- **Contrast:** WCAG AA minimum (4.5:1)
