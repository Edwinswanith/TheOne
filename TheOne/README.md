# GTMGraph

Evidence-backed GTM planning system that converts product ideas into decision-complete execution graphs.

## Screenshots

### Home Screen
![Home Screen](docs/screenshots/home-full.png)

### Project Input Form
![Input Form](docs/screenshots/input-form.png)

### Graph Workspace
![Graph Workspace](docs/screenshots/project-view.png)

## Monorepo Layout

- `apps/web`: Next.js UI shell (React Flow workspace + decision gates)
- `services/api`: FastAPI HTTP API + SSE endpoints
- `services/orchestrator`: canonical state, merge rules, validator, run runtime
- `services/worker`: Celery tasks for async runs
- `services/export`: Markdown + HTML/PDF export renderer
- `packages/shared/schemas`: JSON schemas for canonical state and agent output contracts
- `test`: Product acceptance specs (`TC-001` to `TC-020`)

## Quick Start (Local)

1. Copy `.env.example` to `.env` and set API keys.
2. Start data services: `docker compose up -d`.
3. Install Python dependencies with `uv sync`.
4. Install web dependencies with `pnpm install`.
5. Apply DB migrations: `make migrate`.
6. Start API: `uv run uvicorn services.api.app.main:app --reload`.
7. Start worker: `uv run celery -A services.worker.tasks.run_tasks.celery_app worker --loglevel=info`.
8. Start web: `pnpm --filter web dev`.

## Provider Modes

- Fixture mode (default): `GTMGRAPH_USE_REAL_PROVIDERS=false`
  - Loads deterministic responses from `services/orchestrator/fixtures/`.
  - Used in tests and CI.
- Real mode: `GTMGRAPH_USE_REAL_PROVIDERS=true`
  - Uses Perplexity API for evidence retrieval and Gemini API for synthesis.
  - Requires `perplexity_api_key` and `Google_API_Key`.

## Database + Alembic

- SQL store is enabled by default through `DATABASE_URL`.
- Migrations:
  - `make migrate`
  - `make migration m=\"describe_change\"`
- Initial migration file: `alembic/versions/0001_initial_schema.py`.

## Current Status

Implemented baseline now includes remaining phase mechanics:

- canonical state schema contract and default state init
- merge/validator core logic with deterministic rule checks
- SQL-backed persistence (Postgres-compatible) with snapshots/checkpoints
- Alembic migration scaffolding and initial schema migration
- provider integration layer with feature flags + fixture mode for tests
- run resume, partial rerun, decision overrides, export/compare API flows
- test suite validating core TC behaviors
