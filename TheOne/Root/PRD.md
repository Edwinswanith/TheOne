PRD: GTMGraph

Working name: GTMGraph
Category: Evidence-backed go-to-market planner and execution graph
Core promise: Turn a product idea into a decision-complete, evidence-linked execution plan across 4 business pillars, rendered as a grouped graph with accountable overrides.

Why this exists

Founders can build fast but still fail because they never nail:

Who pays (ICP + trigger)

Why they win (positioning + wedge)

How they charge (pricing metric + packaging)

How they acquire (channel focus + sales motion)

Most “AI business plan” tools generate content. You must generate decisions, proof, and next actions.

1) Goals and non-goals
Goals (V1)

Convert a vague idea into a decision-complete plan in under 30 minutes.

Every major claim must be either:

Evidence-backed with sources, or

Explicitly labeled as an assumption with confidence.

Render outputs as a 4-pillar grouped graph with dependencies and “next action” checklists.

Support overrides without letting users sabotage themselves:

Require justification

Show impact warnings

Support scenario comparison:

Scenario A vs Scenario B with diffs

Non-goals (V1)

Not a full business plan generator with 40 sections.

Not a CRM.

Not a code generator for the entire product.

Not “cover everything.” It must focus on early bottlenecks: buyer, wedge, channel, pricing, and proof of willingness to pay.

2) Pillar model
Top-level pillars (V1)

Market to Money

Product

Execution

People and Cash

The older 6-pillar lists become subnodes inside these pillars. This prevents UI bloat and keeps users focused.

3) ICP and personas
Primary ICP (V1)

Solo founders and small teams (1 to 5) building B2B SaaS or B2B AI services

Strong builders, weak GTM

Will pay to avoid building the wrong thing

Personas (minimum 5)

Technical founder: builds fast, no sales motion, vague ICP

Marketer launching a product: can write, cannot choose ICP or pricing metric

Agency owner productizing: knows services, needs scalable offer and outbound structure

Domain expert non-technical: knows the problem space, lost on GTM and tech feasibility

Startup studio operator: needs repeatable evaluation and execution templates across ideas

Each persona maps to different default recommendations and different “gates.”

4) Product experience and user flow
Screen 1: Project creation

Inputs

Project name

Idea one-liner

Region

Category (B2B SaaS, B2B service, B2C optional but discouraged)

Constraints: time, team, budget

Outcome

Create Project + Scenario A draft

Screen 2: Clarifier questions (adaptive)

This is not a survey. It’s a quality gate.

Question types

MCQ with “recommended” choice

Custom input

“Not sure” triggers deeper probing

Minimum required outputs to proceed

Buyer role and company type

Trigger event (why now)

Current workaround

Measurable outcome

If missing, block “Run” and show what is missing.

Screen 3: Evidence run kickoff

User clicks “Run research and build plan”.

System runs:

Competitor discovery

Substitute mapping (“do nothing”)

Pricing anchors

Messaging patterns

Channel signals

All outputs must link to sources.

Screen 4: Decision gates

User must pick one option per gate to proceed.

Gate A: ICP choice

Option 1 (recommended)

Option 2 (alternative)

Option 3 (niche wedge, optional)

Custom (requires justification)

Gate B: Positioning wedge

Category framing

Primary alternative

Differentiation wedge

Gate C: Pricing hypothesis

Pricing metric (per seat, per usage, per outcome)

2 to 3 tiers

First price-to-test

Gate D: Channel focus

1 primary channel

1 backup channel
More than that is noise. If user insists, mark as “high risk” and demand prioritization.

Gate E: Sales motion

Outbound-led, inbound-led, PLG, partner-led
System blocks contradictions with warnings (example: enterprise ICP with PLG-only and no sales support plan).

Screen 5: Graph workspace

Graph is grouped by pillar. Nodes have:

Output

Assumptions

Confidence score

Evidence links

Next actions

Dependencies

Graph actions

Expand/collapse groups

Scenario toggle (A vs B)

Rerun subtree when assumptions change

Export

React Flow supports nested “sub flows” for grouping and nodes within a parent.

Screen 6: Commit to execution

User must leave with a real action plan. Pick one track:

Validation sprint (2 weeks)

Outbound sprint (first 50 messages)

Landing page + waitlist sprint

Pilot onboarding sprint

Generate assets and checklist, then export.

5) Key differentiators (what makes you not trash)

Evidence-backed outputs by default
No evidence means the node is labeled as assumption with lower confidence.

Decision completeness
User cannot “finish” without choosing: ICP, wedge, pricing metric, channel, sales motion.

Scenario compare
You show trade-offs between two serious plans, not 10 weak options.

Accountable overrides
Overrides require justification and trigger impact warnings and dependency re-evaluation.

Partial reruns
Changing ICP reruns dependent nodes only (pricing, channels, sales), not the entire plan.

6) Agent system design
Orchestration framework

Use LangGraph for V1 because it gives you persistence and checkpointing for stateful runs and “time travel” style debugging, which is exactly what you need for long multi-step workflows.
It also supports memory patterns as part of state.

Alternative is CrewAI Flows, which supports structured workflows and state control.
Pick one for V1. Mixing frameworks early makes debugging miserable.

Canonical shared state (single source of truth)

All agents read and write a shared structured state object.

Top-level state sections

idea: description, constraints, category, region

evidence: competitors, pricing anchors, positioning claims, sources

decisions: ICP, wedge, channel, pricing metric, sales motion

pillars: outputs per pillar, node-by-node

risks: contradictions, missing proof, uncertainty hotspots

execution: next actions, sprint plan, assets generated

telemetry: token spend, agent timing, errors

Field metadata

source_type: evidence | inference | assumption

confidence: 0.0 to 1.0

sources: array of URLs and excerpts

updated_by: agent name

depends_on: list of state paths

Agent lineup (V1 predefined)

Core

Clarifier Agent

Evidence Collector Agent

ICP Agent

Positioning Agent

Pricing Agent

Channel Strategy Agent

Sales Motion Agent

Product Strategy Agent

Tech Architecture Agent

People and Cash Agent

Validator Agent (red-team and contradictions)

Validator responsibilities

Conflict detection

Missing proof flags

“Too many channels” guardrail

“No pricing metric” guardrail

Sales motion mismatch guardrail

How agents communicate

Not by chatting. By publishing structured diffs to the canonical state.

Communication protocol

Each agent outputs a typed payload:

proposed_decisions[]

facts[]

assumptions[]

risks[]

required_inputs[]

node_updates[] (graph nodes)

Orchestrator merges, resolves conflicts, and triggers dependent agents.

Persistence

Use LangGraph checkpointers to persist state per run and thread.
This enables:

Resume after failure

Human-in-the-loop edits

Partial reruns

7) Graph model and node taxonomy
Node types

Decision node

Evidence node

Plan node

Asset node (copy, script, landing page)

Experiment node (hypothesis, steps, pass fail metric)

Risk node

Checklist node

Node fields

id, title, pillar

type

content (structured sections, not one blob)

assumptions[]

confidence

evidence_refs[]

dependencies[]

status: draft | needs-input | final

actions[]: export, rerun, edit, compare

Grouping behavior

Use React Flow subflows for grouping and nested graphs.
Also support selection grouping for manual organization.

8) Look and feel spec
Design principles

Sketch vibe is fine, but readability wins.

High contrast for text and UI components.

WCAG minimum contrast guidance for readable UI is at least 4.5:1 for normal text (AA).
Use a contrast checker during design QA.

Palette (minimal “pencil sketch” theme)

Use tokens so you can theme later:

Background: warm off-white (paper)

Foreground: charcoal

Secondary: graphite gray

Accent 1: muted sage (calm focus)

Accent 2: muted amber (warnings and risk)

Charcoal as a base is widely used as a strong neutral foundation.

Typography

Body and UI: Inter (high legibility, tall x-height, designed for screens).

Headings: Source Serif 4 (serif contrast for “editorial” sketchbook feel).

Key UI components

Left: pillar navigator and scenario switcher

Center: graph canvas

Right drawer: node details, evidence links, confidence, edit and rerun

Top bar: Run status, export, history, compare

9) Tech stack
Frontend

Next.js (TypeScript)

React Flow for graph UI and grouping.

State management: Zustand

Styling: Tailwind CSS

Streaming updates: SSE preferred (simple, reliable) or WebSockets if you need bi-directional control

Auth: Auth.js or Clerk (choose based on speed vs control)

Backend

Python + FastAPI

LangGraph for orchestration and persistence.

Task queue: Celery + Redis

Database: Postgres

Object storage: S3 compatible for exports and evidence snapshots

Observability

OpenTelemetry tracing and FastAPI instrumentation.
This is not optional. Long-running agent runs will fail and you need real traceability.

10) System architecture
Services

api (FastAPI)

Auth session validation

Project and scenario CRUD

Node and evidence CRUD

Run orchestration endpoints

orchestrator

LangGraph workflows

Dependency DAG

State merge and conflict resolution

worker

Runs agents, scraping, summarization, extraction

evidence

Search pipeline

Source scoring

Content extraction

export

PDF and Markdown generation

Core runtime loop

User starts run

Orchestrator builds plan based on required gates

Evidence agent runs first

Decision gates require user input if unresolved

Downstream pillar agents run

Validator runs at each milestone and at end

Graph updates stream to UI

11) API design (concrete)
Projects

POST /projects

GET /projects/:id

GET /projects

PATCH /projects/:id

Scenarios

POST /projects/:id/scenarios

GET /scenarios/:id

PATCH /scenarios/:id

Runs

POST /scenarios/:id/runs (start run)

GET /runs/:id

GET /runs/:id/stream (SSE stream events)

Nodes and evidence

GET /scenarios/:id/nodes

PATCH /nodes/:id (edit content or override decision)

POST /nodes/:id/rerun (rerun subtree)

GET /nodes/:id/evidence

Exports

POST /scenarios/:id/export (pdf, md)

GET /exports/:id

12) Data model (tables)
Minimum tables

users

projects

scenarios

runs

state_snapshots (canonical state JSON, versioned)

nodes

edges

evidence_sources

node_evidence_map

decisions

agent_logs

Why snapshots matter

You need to:

Compare scenarios

Diff runs

Debug why the system recommended something

Support partial reruns safely

13) Repository and file structure
Monorepo
gtmgraph/
  apps/
    web/                      # Next.js
      src/
        app/
        components/
          graph/
          nodes/
          drawers/
          gates/
        lib/
        styles/
        types/
  services/
    api/                      # FastAPI
      app/
        main.py
        routers/
        schemas/              # Pydantic models
        db/
        auth/
        telemetry/
    orchestrator/             # LangGraph graphs + merge logic
      graphs/
      agents/
      state/
      validators/
      tools/
    worker/                   # Celery tasks
      tasks/
      pipelines/
    export/                   # PDF/MD export
      templates/
      renderer/
  packages/
    shared/
      schemas/                # shared JSON schema for nodes, state
      constants/
  infra/
    docker/
    k8s/                      # later
    terraform/                # later
  docs/
    prd/
    api/

Frontend key folders

components/graph: React Flow canvas, layout, interactions

components/gates: decision gates screens

components/drawers: node detail panel

types/: shared node and state types

Backend key folders

orchestrator/state: canonical state types and merge rules

orchestrator/validators: contradiction checks and gating logic

orchestrator/agents: agent implementations, strict structured outputs

orchestrator/tools: search, extraction, scraping, summarization

14) Security and trust

Store evidence snapshots and cite sources so users can audit.

Rate limit runs per user to control cost.

Strict sandboxing for any web extraction code.

Never claim certainty without evidence. Confidence scoring must be visible.

15) Performance requirements

First meaningful output on screen within 30 to 60 seconds: evidence list and initial competitor map.

Stream updates continuously, no “blank waiting”.

Partial reruns must be 3 to 5x faster than full reruns for common changes like ICP swap.

16) Acceptance criteria (MVP exit bar)

A run is considered “complete” only if:

ICP selected

Wedge selected

Pricing metric selected

Primary channel selected

Sales motion selected

Validator reports no critical contradictions

Graph shows at least:

4 pillar groups

20+ nodes total

Evidence links attached to competitor and pricing nodes

User committed to one execution track and exported assets

17) Build plan (concrete milestones)
Milestone 1: Skeleton (Week 1 to 2)

Project/scenario/run model

React Flow canvas with grouping

SSE stream pipeline

Minimal orchestrator with dummy agents

Milestone 2: Evidence engine (Week 3)

Competitor discovery with source links

Pricing anchor extraction

Evidence viewer in node drawer

Milestone 3: Decision gates (Week 4)

ICP, wedge, pricing metric, channel, sales motion gates

Override justification and impact warnings

Milestone 4: Pillar graph and validator (Week 5 to 6)

Generate full pillar graph

Contradiction detection

Partial rerun for ICP changes

Milestone 5: Exports and scenario compare (Week 7)

PDF, Markdown export

Scenario A vs B compare and diff