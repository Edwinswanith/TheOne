# GTMGraph — Execution, Testing & Version Control Plan

## Environment & Tooling

### API Keys (`.env`)
```
Google_API_Key=<your-gemini-key>      # Gemini — all agent reasoning, generation, structured outputs
perplexity_api_key=<your-key>         # Perplexity — evidence collection, competitor discovery, pricing anchors
```

### MCP Tooling
- **Chrome DevTools MCP** (`.mcp.json`) — used for browser-based E2E testing, inspecting SSE streams, auditing React Flow DOM, and verifying WCAG contrast in the running app.

### Repository
- **Remote:** https://github.com/Edwinswanith/TheOne.git
- **Default branch:** `main`

---

## Phase 0: Project Scaffolding (Days 1–2)

### 0.1 Monorepo Setup
```
gtmgraph/
  apps/
    web/                    # Next.js (TypeScript)
  services/
    api/                    # Python FastAPI
    orchestrator/           # LangGraph graphs + agents + merge logic
    worker/                 # Celery tasks
    export/                 # PDF/MD generation
  packages/
    shared/
      schemas/              # JSON Schemas (canonical state, agent output)
      constants/
  infra/
    docker/
  docs/
    prd/                    # Move Root/*.md here
```

### 0.2 Toolchain Init
| Layer | Init Command | Config Files |
|-------|-------------|--------------|
| Frontend | `npx create-next-app@latest apps/web --ts --tailwind --app --src-dir` | `tsconfig.json`, `tailwind.config.ts`, `.eslintrc.json` |
| Backend | `mkdir -p services/api && cd services/api && python -m venv .venv && pip install fastapi uvicorn sqlalchemy alembic pydantic` | `pyproject.toml`, `alembic.ini` |
| Orchestrator | `pip install langgraph langchain-google-genai` | — |
| Worker | `pip install celery[redis]` | `celeryconfig.py` |
| Shared schemas | Copy `Root/*.md` JSON blocks into `.json` files under `packages/shared/schemas/` | `canonical_state.schema.json`, `agent_output.schema.json` |
| Docker | Compose file for Postgres + Redis | `docker-compose.yml` |

### 0.3 Environment Config
```
# .env (root, git-ignored)
Google_API_Key=...
perplexity_api_key=...

DATABASE_URL=postgresql://gtm:gtm@localhost:5432/gtmgraph
REDIS_URL=redis://localhost:6379/0
```

### 0.4 Initial Commit
```
git init
git remote add origin https://github.com/Edwinswanith/TheOne.git
git add .
git commit -m "chore: monorepo scaffold with Next.js, FastAPI, LangGraph, Docker"
git push -u origin main
```

---

## Phase 1: Skeleton — Models, Canvas, SSE, Dummy Agents (Days 3–10)

### 1.1 Database & Models
- Define SQLAlchemy models: `users`, `projects`, `scenarios`, `runs`, `state_snapshots`, `nodes`, `edges`, `evidence_sources`, `node_evidence_map`, `decisions`, `agent_logs`
- Generate Alembic migration
- Seed script: create one test project with default Scenario A

**Validates:** TC-001 (project creation, canonical state initialization)

### 1.2 API Layer (FastAPI)
Build CRUD endpoints in order:
1. `POST /projects` — creates project + default scenario + empty canonical state snapshot
2. `GET /projects/:id`, `GET /projects`, `PATCH /projects/:id`
3. `POST /projects/:id/scenarios`, `GET /scenarios/:id`, `PATCH /scenarios/:id`
4. `POST /scenarios/:id/runs` — start a run (queue to Celery)
5. `GET /runs/:id`, `GET /runs/:id/stream` (SSE)
6. `GET /scenarios/:id/nodes`, `PATCH /nodes/:id`, `POST /nodes/:id/rerun`, `GET /nodes/:id/evidence`
7. `POST /scenarios/:id/export`, `GET /exports/:id`

Pydantic models must match `canonical_state.schema.json` exactly — generate from schema or hand-write with strict validation.

### 1.3 SSE Pipeline
- `GET /runs/:id/stream` returns `text/event-stream`
- Events: `run_started`, `agent_started`, `agent_progress`, `agent_completed`, `node_created`, `node_updated`, `run_completed`, `run_failed`
- Each event carries enough payload to update the frontend graph incrementally

**Validates:** TC-015 (SSE intermediate updates within 10–20s)

### 1.4 Frontend Skeleton
- Project list → create project form (Screen 1)
- React Flow canvas with 4 pillar groups (empty) (Screen 5)
- Left panel: pillar navigator + scenario switcher
- Right drawer: node detail stub
- Top bar: run status, export button (disabled)
- SSE subscription hook: connect to `/runs/:id/stream`, dispatch events to Zustand store

### 1.5 Dummy Agents + Orchestrator Shell
- LangGraph graph definition with 11 agent nodes (all stubs returning hardcoded `AgentOutput`)
- Orchestrator merge loop: apply patches in correct order (Evidence → Decisions → Pillars → Graph → Execution → Telemetry)
- Celery task to run the LangGraph graph and emit SSE events

### 1.6 Git Checkpoint
```
git checkout -b feat/skeleton
# commits along the way
git push -u origin feat/skeleton
# PR → main when phase complete
```

---

## Phase 2: Evidence Engine (Days 11–17)

### 2.1 Perplexity Integration (`services/orchestrator/tools/`)
- `search_competitors(idea, category, region)` → calls Perplexity API with `perplexity_api_key`
- `search_pricing_anchors(competitors)` → pricing model extraction
- `search_messaging_patterns(category, icp)` → messaging/positioning signals
- `search_channel_signals(category, icp)` → channel effectiveness data
- All results return structured JSON with `url`, `title`, `snippets`, `quality_score`

### 2.2 Evidence Collector Agent
- Replace dummy with real Gemini-powered agent
- Agent prompt receives `idea` + `constraints` from canonical state
- Agent calls Perplexity tools, then uses Gemini (`Google_API_Key`) to synthesize structured `AgentOutput`
- Output: `patches[]` targeting `/evidence/*`, `facts[]` with source URLs, `assumptions[]` for unproven claims
- Evidence dedup: merge by normalized URL, keep max `quality_score` (Merge Rule B)

### 2.3 Evidence Viewer
- Node drawer shows evidence links, snippets, quality scores
- Click-through to source URL
- "Assumption" badge for claims without sources

**Validates:**
- TC-005 (evidence source dedup by URL)
- TC-016 (claims without source forced to assumption)
- TC-012 (missing evidence for pricing anchors triggers missing proof)

### 2.4 Git Checkpoint
```
git checkout -b feat/evidence-engine
git push -u origin feat/evidence-engine
# PR → main
```

---

## Phase 3: Clarifier & Decision Gates (Days 18–24)

### 3.1 Clarifier Agent
- Gemini-powered adaptive questioning
- Question types: MCQ with recommended, custom input, "not sure" (triggers deeper probing)
- Minimum outputs to proceed: buyer role, company type, trigger event, current workaround, measurable outcome
- If missing → block "Run" button, show what's missing

**Validates:**
- TC-002 (intake gate blocks run when buyer role missing)
- TC-003 (MCQ recommended option saves without justification)

### 3.2 Decision Gate UI (Screen 4)
Five sequential gates, each presenting 1–3 options + custom:

| Gate | Agent | Decision Key |
|------|-------|-------------|
| A: ICP | ICP Agent | `decisions.icp` |
| B: Positioning | Positioning Agent | `decisions.positioning` |
| C: Pricing | Pricing Agent | `decisions.pricing` |
| D: Channels | Channel Strategy Agent | `decisions.channels` |
| E: Sales Motion | Sales Motion Agent | `decisions.sales_motion` |

- Each agent outputs `DecisionProposal` with options, pros/cons, risks
- Orchestrator presents to user, user picks (or enters custom)
- Custom requires justification text → stored as override

### 3.3 Override System
- Custom override → requires justification (block without it)
- Generate and store impact warning showing which downstream nodes will be affected
- Trigger partial rerun of dependent agents

**Validates:**
- TC-004 (custom override requires justification, blocks without it)
- TC-007 (decision ownership — only orchestrator writes `selected_option_id`)
- TC-018 (override impact warning generated and stored)

### 3.4 Git Checkpoint
```
git checkout -b feat/decision-gates
git push -u origin feat/decision-gates
# PR → main
```

---

## Phase 4: Pillar Agents, Full Graph & Validator (Days 25–38)

### 4.1 Remaining Agents (Gemini-powered)
Replace dummies with real implementations:
- **ICP Agent** — buyer profile synthesis from evidence + inputs
- **Positioning Agent** — category framing, wedge, value prop
- **Pricing Agent** — metric, tiers, first-price-to-test from pricing anchors
- **Channel Strategy Agent** — primary + secondary channel from signals
- **Sales Motion Agent** — motion type from ICP + channel decisions
- **Product Strategy Agent** — feature planning, competitive positioning
- **Tech Architecture Agent** — tech feasibility assessment
- **People and Cash Agent** — team requirements, runway calculation

Each agent:
1. Reads relevant canonical state sections
2. Calls Gemini with structured output schema
3. Returns `AgentOutput` with patches, node_updates, facts, assumptions, risks

### 4.2 Orchestrator: Merge & Dependency DAG
- Apply Merge Rules A–F from spec
- Dependency ordering: evidence → ICP → positioning → pricing → channels → sales motion → pillar agents → graph → execution
- Partial rerun: when ICP changes, only rerun pricing, channels, sales motion, and dependent pillar agents (not evidence)

**Validates:**
- TC-006 (patch ordering preserves dependencies)
- TC-008 (conflicting evidence creates candidates + validator item)
- TC-013 (partial rerun only recomputes dependent nodes after ICP change)
- TC-014 (node ID stability prevents duplicates)

### 4.3 Full Graph Generation
- Generate 20+ nodes across 4 pillar groups
- Stable node IDs: `market.icp.summary`, `pricing.metric`, `sales.pipeline`, etc.
- Edges: `depends_on`, `informs`, `blocks`
- React Flow renders grouped graph with expand/collapse

### 4.4 Validator Agent
Implement all 14 V1 rules from conflict matrix:

| Rule | Severity | Check |
|------|----------|-------|
| V-ICP-01 | Critical | ICP empty + finalize → block |
| V-PROD-01 | Critical | Value prop missing + pillar finalize → block |
| V-PRICE-01 | Critical | Pricing metric empty + tiers exist → block |
| V-CHAN-01 | High | >2 primary channels + B2B → focus failure |
| V-SALES-01 | High | PLG + enterprise ICP → mismatch |
| V-SALES-02 | Medium | Outbound + SMB + low price → unit economics warn |
| V-PRICE-02 | High | High price + no WTP proof → missing proof |
| V-TECH-01 | Critical | High compliance + no security plan → block |
| V-EVID-01 | High | Empty competitors + non-novel → missing proof |
| V-EVID-02 | High | Empty pricing anchors + pricing decided → missing proof |
| V-EXEC-01 | High | Track unset + export final → block export |
| V-OPS-01 | High | Execution pillar empty + mark complete → block |
| V-PEOPLE-01 | Medium | People/cash empty + pricing decided → runway warn |
| V-CONT-01 | High | Override + no justification → block |

Outputs to `state.risks.contradictions[]` with `rule_id`, `severity`, `message`, `paths`.

**Validates:**
- TC-009 (validator blocks when pricing metric missing)
- TC-010 (validator flags PLG + enterprise ICP)
- TC-011 (>2 primary channels triggers focus failure)

### 4.5 Checkpoint Persistence
- LangGraph checkpointers save state per run
- Resume from checkpoint after worker failure

**Validates:** TC-019 (run resume from checkpoint after worker failure)

### 4.6 Git Checkpoint
```
git checkout -b feat/pillar-agents-validator
git push -u origin feat/pillar-agents-validator
# PR → main
```

---

## Phase 5: Exports, Execution Track & Scenario Compare (Days 39–45)

### 5.1 Execution Track Selection (Screen 6)
- User picks one track: validation sprint, outbound sprint, landing+waitlist, pilot onboarding
- Generate assets and checklist per track
- Block export until track selected

**Validates:** TC-017 (export blocked until execution track selected)

### 5.2 Export Service
- PDF and Markdown generation from canonical state
- Include: graph summary, decisions with evidence, risks, next actions, assets
- Block final export if validator has critical contradictions

### 5.3 Scenario Compare
- Scenario A vs B diff view
- Highlight decision differences, confidence changes, risk delta

### 5.4 Schema Enforcement
- Reject unknown root keys in canonical state on every write
- JSON Schema validation at API boundary

**Validates:** TC-020 (schema enforcement rejects unknown root keys)

### 5.5 Git Checkpoint
```
git checkout -b feat/exports-compare
git push -u origin feat/exports-compare
# PR → main
```

---

## Testing Strategy

### Unit Tests (per phase)
| Layer | Framework | What to test |
|-------|-----------|-------------|
| Backend API | `pytest` + `httpx` | Every endpoint, request/response validation, auth guards |
| Orchestrator | `pytest` | Merge rules A–F individually, patch ordering, conflict resolution, confidence aggregation |
| Agents | `pytest` | Each agent returns valid `AgentOutput` schema, handles empty/partial state |
| Validator | `pytest` | Each of the 14 rules fires correctly with synthetic state |
| Frontend | `vitest` + `@testing-library/react` | Zustand store logic, SSE event handling, gate form validation |

### Integration Tests
| Test | Method |
|------|--------|
| Project creation → canonical state init | API call + DB assertion (TC-001) |
| Full run: evidence → decisions → graph | Celery task with real Gemini + Perplexity calls against test idea |
| SSE streaming | Subscribe to stream endpoint, assert events arrive within 60s (TC-015) |
| Partial rerun | Change ICP after full run, verify only dependent nodes recompute (TC-013) |
| Checkpoint resume | Kill worker mid-run, restart, verify resume (TC-019) |

### E2E Tests (Chrome MCP)
Use Chrome DevTools MCP to automate browser testing:

| Test | Chrome MCP Usage |
|------|-----------------|
| Project creation flow | Navigate to /new, fill form, submit, verify redirect to workspace |
| Clarifier gate blocking | Attempt to click "Run" with missing buyer role, verify UI blocks (TC-002) |
| Decision gate flow | Walk through all 5 gates, pick options, verify graph updates |
| Override flow | Pick custom option without justification, verify block; add justification, verify acceptance (TC-004) |
| Graph rendering | Inspect React Flow DOM: verify 4 groups, 20+ nodes, edges, expand/collapse |
| SSE real-time updates | Start run, verify graph nodes appear incrementally without page refresh |
| Export blocking | Try export with track unset, verify blocked (TC-017) |
| WCAG contrast | Audit computed styles for text elements, verify 4.5:1 minimum ratio |

### Test Case → Phase Mapping

| TC | Phase | Description |
|----|-------|-------------|
| TC-001 | 1 | Project + canonical state init |
| TC-002 | 3 | Intake gate blocks when buyer role missing |
| TC-003 | 3 | MCQ recommended saves without justification |
| TC-004 | 3 | Custom override requires justification |
| TC-005 | 2 | Evidence dedup by URL |
| TC-006 | 4 | Patch ordering preserves dependencies |
| TC-007 | 3 | Decision ownership enforcement |
| TC-008 | 4 | Conflicting evidence creates candidates |
| TC-009 | 4 | Validator blocks when pricing metric missing |
| TC-010 | 4 | Validator flags PLG + enterprise ICP |
| TC-011 | 4 | >2 primary channels triggers focus failure |
| TC-012 | 2 | Missing evidence for pricing anchors |
| TC-013 | 4 | Partial rerun only recomputes dependent nodes |
| TC-014 | 4 | Node ID stability prevents duplicates |
| TC-015 | 1 | SSE intermediate updates |
| TC-016 | 2 | Claim without source forced to assumption |
| TC-017 | 5 | Export blocked until track selected |
| TC-018 | 3 | Override impact warning stored |
| TC-019 | 4 | Run resume from checkpoint |
| TC-020 | 5 | Schema enforcement rejects unknown keys |

---

## Version Control Strategy

### Branch Model
```
main                          ← stable, deployable
  └── feat/skeleton           ← Phase 1
  └── feat/evidence-engine    ← Phase 2
  └── feat/decision-gates     ← Phase 3
  └── feat/pillar-agents-validator  ← Phase 4
  └── feat/exports-compare    ← Phase 5
  └── fix/*                   ← hotfixes off main
```

### Commit Convention
```
<type>(<scope>): <description>

Types: feat, fix, refactor, test, chore, docs
Scopes: api, web, orchestrator, worker, export, shared, infra
```
Examples:
- `feat(api): add POST /projects endpoint with canonical state init`
- `feat(orchestrator): implement evidence dedup merge rule B`
- `test(validator): add V-SALES-01 PLG+enterprise mismatch test`
- `fix(web): SSE reconnection on connection drop`

### PR Workflow
1. Create feature branch from `main`
2. Push commits with descriptive messages
3. Open PR on GitHub with summary + test plan
4. All unit tests must pass before merge
5. Squash merge into `main`

### Release Tags
```
v0.1.0  — Phase 1 complete (skeleton)
v0.2.0  — Phase 2 complete (evidence engine)
v0.3.0  — Phase 3 complete (decision gates)
v0.4.0  — Phase 4 complete (full graph + validator)
v0.5.0  — Phase 5 complete (exports + compare) = MVP
```

### Protected Files
Never commit to the repo:
- `.env` (API keys) — listed in `.gitignore`
- `*.pem`, `*.key`, credentials files
- `node_modules/`, `__pycache__/`, `.venv/`

### .gitignore (root)
```
.env
.env.*
node_modules/
__pycache__/
.venv/
*.pyc
.next/
dist/
*.egg-info/
.DS_Store
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Gemini rate limits during parallel agent runs | Queue agents through Celery with configurable concurrency; add exponential backoff |
| Perplexity API quota exhaustion | Cache evidence results in DB by normalized URL; skip re-fetch within 24h |
| SSE connection drops | Frontend auto-reconnect with `Last-Event-ID` header; backend replays missed events |
| State corruption from bad merge | Snapshot canonical state before every merge; rollback on validation failure |
| Long agent runs (>60s) | Stream intermediate results; timeout individual agents at 45s with partial output |
