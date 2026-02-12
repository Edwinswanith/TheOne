# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**GTMGraph** — an evidence-backed go-to-market planner that turns a product idea into a decision-complete, evidence-linked execution plan across 6 business pillars, rendered as a two-level grouped graph with accountable overrides.

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
make api                      # FastAPI server (uvicorn --reload, default :8000)
make worker                   # Celery worker (services.worker.tasks.run_tasks.celery_app)
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

### Linting
```bash
uv run ruff check services/   # Python lint (line-length=100, runs in CI)
pnpm web:lint                 # Frontend lint (runs in CI)
```

### Database
```bash
make migrate                              # Apply migrations
make migration m="describe_change"        # Create new migration
```

## Architecture

### Monorepo Layout
- `apps/web/` — Next.js (TypeScript), React Flow graph, Zustand state, Tailwind CSS
- `services/api/` — FastAPI HTTP API + SSE streaming
- `services/orchestrator/` — Core business logic: agents, merge engine, validator, runtime pipeline
- `services/orchestrator/chat/` — Conversational intake chat module
- `services/worker/` — Celery tasks for async run execution
- `services/export/` — Markdown + HTML export renderer
- `packages/shared/schemas/` — JSON Schemas (`canonical_state.schema.json`, `agent_output.schema.json`)
- `Root/` — Product specs (PRD, schemas, validator rules) — source of truth for requirements
- `test/` — Product acceptance test cases (TC-001 to TC-020)

### API (`services/api/app/main.py`)
All routes are defined in a single file (no router modules). Key endpoint groups:

**Projects:**
- `POST /projects` — Create a project (name + idea)
- `POST /projects/from-context` — Create project from free-form context (Gemini extracts structure, pre-populates intake)
- `GET /projects` — List all projects
- `GET /projects/{id}` — Get single project
- `PATCH /projects/{id}` — Update project name

**Scenarios:**
- `POST /projects/{id}/scenarios` — Create new scenario under a project
- `GET /scenarios/{id}` — Get scenario with full state
- `PATCH /scenarios/{id}` — Update scenario name

**Intake (three paths):**
- `POST /scenarios/{id}/chat` — Conversational chat intake (primary)
- `POST /scenarios/{id}/clarification` — Generate clarification questions
- `POST /scenarios/{id}/clarification/submit` — Submit clarification answers
- `GET /scenarios/{id}/intake/questions` — Generate MCQ intake questions (fallback)
- `POST /scenarios/{id}/intake` — Submit MCQ intake answers (fallback)

**Runs:**
- `POST /scenarios/{id}/runs` — Start a pipeline run
- `POST /runs/{id}/resume` — Resume a failed run from checkpoint
- `GET /runs/{id}` — Get run status
- `GET /runs/{id}/stream` — SSE event stream

**Decisions & Nodes:**
- `POST /scenarios/{id}/decisions/{key}/select` — Override a decision with justification
- `PATCH /scenarios/{id}/execution-track` — Set execution track
- `GET /scenarios/{id}/nodes` — Get graph nodes for a scenario
- `PATCH /nodes/{id}` — Patch individual node content
- `POST /nodes/{id}/rerun` — Rerun analysis for a node (partial pipeline)
- `GET /nodes/{id}/evidence` — Get evidence for a node

**Completion & Export:**
- `POST /scenarios/{id}/complete` — Mark scenario complete (validator blocks if critical issues)
- `POST /scenarios/{id}/export` — Export scenario (md or html, draft or final)
- `GET /exports/{id}` — Get export content
- `POST /scenarios/compare` — Side-by-side scenario comparison

**Utility:**
- `POST /audio/transcribe` — Audio transcription via GROQ Whisper (25 MB limit)

Request/response models in `schemas.py`. SQLAlchemy ORM models in `db_models.py`.

### Intake Flow
Three intake paths exist:

**Primary — Conversational chat** (`services/orchestrator/chat/intake_chat.py`):
Turn-by-turn chat where Gemini asks one adaptive question at a time, collecting the 5 required fields: `buyer_role`, `company_type`, `trigger_event`, `current_workaround`, `measurable_outcome`. Tracks readiness (0.0–1.0). When `from-context` creation is used, the chat adapts questions based on already-inferred context.

**Secondary — MCQ clarification** (`/scenarios/{id}/clarification`):
Gemini generates structured multiple-choice clarification questions grouped by category (customer, market, value, product, execution). Each question supports `allow_custom` text input and recommended options include `reasoning` text shown on hover. Answers are mapped to intake fields. Used by the `mcq-intake.tsx` component.

**Fallback — Direct MCQ intake** (legacy):
5 multiple-choice questions generated by Gemini (3 options each, one "recommended", plus custom input). Falls back to static text fields if generation fails. Voice transcription available via GROQ Whisper.

Runs are blocked until intake is complete via any path.

### Agent Architecture
Agents have two modes controlled by `GTMGRAPH_USE_REAL_PROVIDERS`:

- **Real agents** (`services/orchestrator/agents/base.py`): Subclass `BaseAgent` ABC with `build_prompt()` and `parse_response()`. The base `run()` method orchestrates prompt → LLM call (with retry) → parse → `AgentOutput`.
- **Stub agents** (`services/orchestrator/agents/stub_agents.py`): Return deterministic fixture data for tests and development.

`services/orchestrator/agents/registry.py` dispatches between them: `build_agent_output()` checks `GTMGRAPH_USE_REAL_PROVIDERS`, tries real agent, falls back to stub on failure.

### Provider System (Fixture vs Real)
Controlled by `GTMGRAPH_USE_REAL_PROVIDERS` env var in `services/orchestrator/tools/providers.py`:
- **Fixture mode** (default, `false`): Reads deterministic JSON from `services/orchestrator/fixtures/{gemini,perplexity}/`. Used in tests and CI.
- **Real mode** (`true`): Calls Perplexity API (`sonar-pro`) for evidence retrieval and Gemini API (`gemini-2.0-flash`) for synthesis.

### Canonical State
Single source of truth JSON object flowing through the system. Schema: `packages/shared/schemas/canonical_state.schema.json`. Top-level keys: `meta`, `idea`, `constraints`, `inputs`, `evidence`, `decisions`, `pillars`, `graph`, `risks`, `execution`, `telemetry`. Every state mutation is validated via `services/orchestrator/state/validation.py` and snapshotted.

### Pipeline Runtime (`services/orchestrator/runtime.py`)
Runs 13 agents sequentially per `AGENT_SEQUENCE` in `services/orchestrator/dependencies.py`:
`evidence_collector → competitive_teardown_agent → icp_agent → positioning_agent → pricing_agent → channel_agent → sales_motion_agent → product_strategy_agent → tech_feasibility_agent → people_cash_agent → execution_agent → graph_builder → validator_agent`

Two-pass pipeline:
1. **Pass 1:** Runs each agent, merges outputs, auto-recommends decision options after each agent.
2. **Reconciliation pass:** Validator identifies contradictions, maps them to responsible agents via `_PATH_TO_AGENT`, reruns only those agents, then re-runs `graph_builder` + `validator_agent`.

Each agent produces an `AgentOutput` with: `patches` (JSON Patches), `proposals` (decision options), `facts` (evidence-backed claims), `assumptions` (unproven hypotheses), `risks`, `required_inputs`, `node_updates`, `execution_time_ms`, `token_usage` (input_tokens, output_tokens, model). The merge engine (`services/orchestrator/state/merge.py`) applies outputs deterministically. Token usage is aggregated into `state.telemetry.token_spend` by the runtime.

### Merge Rules (Critical — read `merge.py` before modifying)
- **Decision ownership:** Only orchestrator/runtime can write `decisions.*.selected_option_id` — agents submit proposals only
- **Patch ordering:** Evidence → Decisions → Pillars → Graph → Execution → Telemetry
- **Evidence dedup:** Merge by normalized URL, keep max quality score (`services/orchestrator/tools/evidence.py`)
- **Conflict resolution:** Evidence > Inference > Assumption; two evidence sources on same path → create candidates + validator contradiction
- **Node ID stability:** Stable IDs like `market.icp.summary` — upsert by ID, never duplicate
- **Source-less claims:** Evidence patches without sources auto-downgrade to assumption (confidence capped at 0.6)

### Dependency DAG (`services/orchestrator/dependencies.py`)
`DECISION_DEPENDENCY_GRAPH` maps which decisions cascade: changing ICP reruns pricing, channels, sales_motion, positioning. `DECISION_TO_AGENTS` maps decisions to the agents that must re-execute. `ALWAYS_RUN_AGENTS = {graph_builder, validator_agent}`.

### Validator (`services/orchestrator/validators/rules.py`)
14 rules from the conflict matrix: V-ICP-01, V-PROD-01, V-PRICE-01, V-PRICE-02, V-CHAN-01, V-SALES-01, V-SALES-02, V-TECH-01, V-EXEC-01, V-OPS-01, V-PEOPLE-01, V-EVID-01, V-EVID-02, V-CONT-01. Critical/high severity rules block completion/export. Validator writes to `state.risks.contradictions[]`.

### SSE Streaming
`GET /runs/{run_id}/stream` returns `text/event-stream`. Events: `run_started`, `agent_started`, `agent_progress`, `agent_completed`, `state_checkpointed`, `node_created`, `node_updated`, `validator_warning`, `run_blocked`, `run_completed`, `run_failed`, `run_resumed`. Frontend subscribes via `apps/web/src/lib/sse.ts`.

### API Store
`services/api/app/store.py` provides `MemoryStore` (in-memory). Default database is SQLite (`artifacts/gtmgraph.db`); Postgres via `DATABASE_URL` env var for production. `db_models.py` defines SQLAlchemy models for persistence. State snapshots are versioned per run for diffing and rollback.

### Frontend State (`apps/web/src/lib/store.ts`)
Zustand store tracks navigation via `screen`: `"home" | "chat" | "mcq" | "workspace" | "decisions"`.

Key state groups:
- **Projects:** `projects`, `createProject()`, `createFromContext()` (with progress tracking)
- **Chat intake:** `chatMessages`, `chatField`, `chatSuggestions`, `chatReadiness`, `initChat()`, `sendChatMessage()`
- **MCQ intake:** `mcqQuestions`, `mcqAnswers`, `loadMcqQuestions()`, `setMcqAnswer()`, `submitMcq()`
- **Run:** `runId`, `runStatus`, `agentStatuses` (13 agents), SSE `events`, `resumeRun()`
- **Graph:** `nodes`, `groups` (derived from `scenarioState`), `expandedPillar`, `setExpandedPillar()`
- **Detail drawer:** `selectedNodeId`, `selectNode()`

Flow: Home → (create project) → Chat or MCQ intake → Workspace → (start run) → Decisions screen

### Frontend Components (`apps/web/src/components/`)
- `landing-page.tsx` — Landing / marketing page
- `home-screen.tsx` — Project list and creation form
- `chat-intake.tsx` — Conversational chat intake (primary)
- `mcq-intake.tsx` — MCQ clarification intake
- `workspace-shell.tsx` — Main workspace container
- `graph-canvas.tsx` — React Flow canvas with Level 1 (6 pillar cards) → Level 2 (detail nodes on click) drill-down
- `node-drawer.tsx` — Node detail drawer (evidence, assumptions, actions)
- `sidebar.tsx` — Pillar navigator and scenario switcher
- `top-bar.tsx` — Run controls, status indicator, export button
- `run-timeline.tsx` — Live agent execution timeline
- `decision-gate.tsx` — Post-run decision review screen
- `scenario-compare.tsx` — Side-by-side scenario comparison
- `execution-track-picker.tsx` — Execution track selection

## Key Design Constraints
- Graph nodes use stable IDs (e.g., `market.icp.summary`) — never random UUIDs for domain nodes
- Every claim must be evidence-backed or labeled assumption with confidence 0.0–1.0
- Overrides require justification text and generate stored impact warnings with dependency cascade
- Partial reruns recompute only dependent agents (not the full pipeline)
- 6-pillar model: **Market Intelligence**, **Customer**, **Positioning & Pricing**, **Go-to-Market**, **Product & Tech**, **Execution**
- Python >=3.12 required; Ruff line-length 100

## ID Conventions
- Projects: `proj_{uuid.hex}` | Scenarios: `scn_{uuid.hex}` | Runs: `run_{uuid.hex}`
- Exports: `exp_{uuid.hex}` | Snapshots: `ss_{uuid.hex}`
- Nodes: Stable semantic IDs (e.g., `market.icp.summary`, `pricing.metric`, `sales.motion`)

## Test Patterns
Tests in `services/orchestrator/tests/` and `services/api/tests/`. Common helpers:
- `base_state()` — Creates default canonical state
- `patch(path, value, source_type, confidence, sources)` — Creates agent patches
- Fixtures in `services/orchestrator/fixtures/{gemini,perplexity}/` for deterministic testing
- pytest configured with `pythonpath=["."]` and `testpaths` pointing to both test dirs

## Environment Variables (`.env`)
```
Google_API_Key=              # Gemini API (gemini-2.0-flash)
perplexity_api_key=          # Perplexity API (sonar-pro)
GROQ_API_KEY=                # GROQ Whisper API for audio transcription
DATABASE_URL=                # Default: sqlite+pysqlite:///./artifacts/gtmgraph.db
                             # Production: postgresql+psycopg://gtm:gtm@localhost:5432/gtmgraph
REDIS_URL=redis://localhost:6379/0
GTMGRAPH_USE_REAL_PROVIDERS=false
GTMGRAPH_PROVIDER_FIXTURE_ROOT=services/orchestrator/fixtures
```

## CI
GitHub Actions (`.github/workflows/ci.yml`): 4 jobs on push to main and PRs:
- `python-tests` — `uv run pytest -q`
- `python-lint` — `uv run ruff check services/`
- `web-lint` — `pnpm web:lint`
- `web-build` — `pnpm web:build`

## Design System
- **Theme:** Pencil sketch — warm off-white background, charcoal foreground, muted sage accent, muted amber for warnings
- **Typography:** Inter (body/UI), Source Serif 4 (headings)
- **Contrast:** WCAG AA minimum (4.5:1)
