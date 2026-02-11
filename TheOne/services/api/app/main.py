from __future__ import annotations

import json
import os
from copy import deepcopy
from typing import Any

import httpx
from fastapi import BackgroundTasks, FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from services.api.app.schemas import (
    ChatMessageRequest,
    DecisionSelectRequest,
    ExecutionTrackRequest,
    ExportRequest,
    IntakeSubmitRequest,
    ProjectCreateRequest,
    ProjectFromContextRequest,
    ProjectPatchRequest,
    RunResponse,
    RunStartRequest,
    RunStatusResponse,
    ScenarioCompareRequest,
    ScenarioCreateRequest,
    ScenarioPatchRequest,
)
from services.api.app.sse import EventBus
from services.api.app.store import MemoryStore, Run, Scenario
from services.export.renderer import render_html_export, render_markdown_export
from services.orchestrator.dependencies import impacted_decisions
from services.orchestrator.chat.intake_chat import (
    REQUIRED_FIELDS as CHAT_REQUIRED_FIELDS,
    compute_readiness,
    extract_field_prompt,
    fixture_chat_response,
    fixture_extract,
    next_field,
    next_question_prompt,
)
from services.orchestrator.tools.providers import ProviderClient
from services.orchestrator.runtime import PipelineFailure, run_pipeline
from services.orchestrator.state.default_state import create_default_state
from services.orchestrator.state.validation import StateValidationError, validate_state
from services.orchestrator.validators.rules import run_validator

app = FastAPI(title="GTMGraph API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = MemoryStore()
bus = EventBus()

REQUIRED_INTAKE_FIELDS = [
    "buyer_role",
    "company_type",
    "trigger_event",
    "current_workaround",
    "measurable_outcome",
]
DECISION_KEYS = {"icp", "positioning", "pricing", "channels", "sales_motion"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


MAX_AUDIO_SIZE = 25 * 1024 * 1024  # 25 MB


@app.post("/audio/transcribe")
async def transcribe_audio(file: UploadFile) -> dict[str, str]:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured")

    contents = await file.read()
    if len(contents) > MAX_AUDIO_SIZE:
        raise HTTPException(status_code=413, detail="Audio file exceeds 25 MB limit")

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": (file.filename or "audio.webm", contents, file.content_type or "audio/webm")},
            data={"model": "whisper-large-v3"},
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Transcription service error")

    return {"text": resp.json().get("text", "")}


@app.post("/projects")
async def create_project(payload: ProjectCreateRequest) -> dict[str, Any]:
    project = store.create_project(payload.project_name)
    scenario_state = create_default_state(
        project_id=project.id,
        scenario_id="pending",
        idea=payload.idea.model_dump(),
        constraints=payload.constraints.model_dump(),
    )

    scenario = store.create_scenario(project.id, "Scenario A", scenario_state)
    scenario.state["meta"]["scenario_id"] = scenario.id
    scenario.state["meta"]["project_id"] = project.id
    _commit_state(scenario, run_id="unset")

    return {
        "project": {
            "id": project.id,
            "name": project.name,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
        },
        "scenario": {
            "id": scenario.id,
            "name": scenario.name,
            "created_at": scenario.created_at,
            "updated_at": scenario.updated_at,
        },
    }


@app.post("/projects/from-context")
async def create_project_from_context(payload: ProjectFromContextRequest) -> dict[str, Any]:
    provider = ProviderClient()
    extracted = provider.extract_project_from_context(payload.context)

    idea_data = extracted.get("idea", {})
    constraints_data = extracted.get("constraints", {})
    pre_collected = extracted.get("pre_collected_fields", {})

    # Use provided project name or extracted or fallback
    project_name = payload.project_name or extracted.get("project_name") or idea_data.get("name", "New Project")

    # Fill in defaults for idea
    idea = {
        "name": idea_data.get("name", project_name),
        "one_liner": idea_data.get("one_liner", ""),
        "problem": idea_data.get("problem", ""),
        "target_region": idea_data.get("target_region", "US"),
        "category": idea_data.get("category", "b2b_saas"),
    }

    # Fill in defaults for constraints
    constraints = {
        "team_size": int(constraints_data.get("team_size", 2)),
        "timeline_weeks": int(constraints_data.get("timeline_weeks", 8)),
        "budget_usd_monthly": float(constraints_data.get("budget_usd_monthly", 1000)),
        "compliance_level": constraints_data.get("compliance_level", "none"),
    }

    project = store.create_project(project_name)
    scenario_state = create_default_state(
        project_id=project.id,
        scenario_id="pending",
        idea=idea,
        constraints=constraints,
    )

    # Store raw context in inputs
    scenario_state["inputs"]["raw_context"] = payload.context

    # Pre-populate intake answers from extracted fields
    intake_answers = []
    for field_id, field_data in pre_collected.items():
        intake_answers.append({
            "question_id": field_id,
            "answer_type": "text",
            "value": field_data.get("value", ""),
            "meta": {
                "source_type": "inference",
                "confidence": field_data.get("confidence", 0.7),
                "sources": [],
            },
        })
    scenario_state["inputs"]["intake_answers"] = intake_answers

    scenario = store.create_scenario(project.id, "Scenario A", scenario_state)
    scenario.state["meta"]["scenario_id"] = scenario.id
    scenario.state["meta"]["project_id"] = project.id
    _commit_state(scenario, run_id="unset")

    return {
        "project": {
            "id": project.id,
            "name": project.name,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
        },
        "scenario": {
            "id": scenario.id,
            "name": scenario.name,
            "created_at": scenario.created_at,
            "updated_at": scenario.updated_at,
        },
        "pre_collected_fields": sorted(pre_collected.keys()),
    }


@app.get("/projects")
async def list_projects() -> list[dict[str, Any]]:
    return [
        {
            "id": project.id,
            "name": project.name,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "scenario_ids": [s.id for s in store.scenarios.values() if s.project_id == project.id],
        }
        for project in store.projects.values()
    ]


@app.get("/projects/{project_id}")
async def get_project(project_id: str) -> dict[str, Any]:
    project = store.projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="project not found")

    scenarios = [scenario for scenario in store.scenarios.values() if scenario.project_id == project_id]
    return {
        "id": project.id,
        "name": project.name,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "scenario_count": len(scenarios),
    }


@app.patch("/projects/{project_id}")
async def patch_project(project_id: str, payload: ProjectPatchRequest) -> dict[str, Any]:
    if project_id not in store.projects:
        raise HTTPException(status_code=404, detail="project not found")
    project = store.patch_project(project_id, payload.project_name)
    return {
        "id": project.id,
        "name": project.name,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }


@app.post("/projects/{project_id}/scenarios")
async def create_scenario(project_id: str, payload: ScenarioCreateRequest) -> dict[str, Any]:
    if project_id not in store.projects:
        raise HTTPException(status_code=404, detail="project not found")

    project = store.projects[project_id]
    state = create_default_state(
        project_id=project_id,
        scenario_id="pending",
        idea={
            "name": project.name,
            "one_liner": project.name,
            "problem": "",
            "target_region": "",
            "category": "b2b_saas",
        },
        constraints={"team_size": 1, "timeline_weeks": 1, "budget_usd_monthly": 0, "compliance_level": "none"},
    )
    scenario = store.create_scenario(project_id, payload.name, state)
    scenario.state["meta"]["scenario_id"] = scenario.id
    _commit_state(scenario, run_id="unset")

    return {
        "id": scenario.id,
        "project_id": project_id,
        "name": scenario.name,
        "created_at": scenario.created_at,
    }


@app.get("/scenarios/{scenario_id}")
async def get_scenario(scenario_id: str) -> dict[str, Any]:
    scenario = store.scenarios.get(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="scenario not found")
    return {
        "id": scenario.id,
        "project_id": scenario.project_id,
        "name": scenario.name,
        "created_at": scenario.created_at,
        "updated_at": scenario.updated_at,
        "state": scenario.state,
    }


@app.patch("/scenarios/{scenario_id}")
async def patch_scenario(scenario_id: str, payload: ScenarioPatchRequest) -> dict[str, Any]:
    if scenario_id not in store.scenarios:
        raise HTTPException(status_code=404, detail="scenario not found")
    scenario = store.patch_scenario(scenario_id, payload.name)
    return {
        "id": scenario.id,
        "project_id": scenario.project_id,
        "name": scenario.name,
        "updated_at": scenario.updated_at,
    }


@app.get("/scenarios/{scenario_id}/intake/questions")
async def get_intake_questions(scenario_id: str) -> dict[str, Any]:
    scenario = _get_scenario(scenario_id)

    # Return cached questions if already generated
    cached = scenario.state["inputs"].get("intake_questions")
    if cached:
        return {"scenario_id": scenario_id, "questions": cached}

    # Generate via provider
    provider = ProviderClient()
    questions = provider.generate_intake_questions(scenario.state)

    # Persist in state
    scenario.state["inputs"]["intake_questions"] = questions
    scenario.state["meta"]["updated_at"] = store.now().isoformat()
    _commit_state(scenario, scenario.state["meta"].get("run_id", "unset"))

    return {"scenario_id": scenario_id, "questions": questions}


@app.post("/scenarios/{scenario_id}/intake")
async def submit_intake(scenario_id: str, payload: IntakeSubmitRequest) -> dict[str, Any]:
    scenario = _get_scenario(scenario_id)

    serialized_answers: list[dict[str, Any]] = []
    for answer in payload.answers:
        item = answer.model_dump(exclude={"is_recommended"}, exclude_none=True)
        if answer.answer_type == "mcq" and answer.is_recommended:
            item["justification"] = item.get("justification") or ""
        serialized_answers.append(item)

    scenario.state["inputs"]["intake_answers"] = serialized_answers
    scenario.state["meta"]["updated_at"] = store.now().isoformat()
    _commit_state(scenario, run_id=scenario.state["meta"].get("run_id", "unset"))

    return {
        "scenario_id": scenario_id,
        "intake_answers": len(serialized_answers),
        "open_questions": scenario.state["inputs"].get("open_questions", []),
    }


@app.post("/scenarios/{scenario_id}/chat")
async def chat_intake(scenario_id: str, payload: ChatMessageRequest) -> dict[str, Any]:
    """Conversational intake: AI asks one question at a time, extracts structured fields."""
    scenario = _get_scenario(scenario_id)
    provider = ProviderClient()
    idea = scenario.state.get("idea", {})
    constraints = scenario.state.get("constraints", {})

    # Init chat_history in state if missing
    if "chat_history" not in scenario.state["inputs"]:
        scenario.state["inputs"]["chat_history"] = []

    history = scenario.state["inputs"]["chat_history"]

    # Determine which fields are already collected
    collected = {
        a.get("question_id", "")
        for a in scenario.state["inputs"].get("intake_answers", [])
        if a.get("value") and str(a["value"]).strip()
    }

    # Record user message
    history.append({"role": "user", "content": payload.message})

    # Determine current field being asked
    current_field = payload.field_context or next_field(collected)

    # Extract structured answer from user message
    if current_field and current_field not in collected:
        if provider.config.use_real_providers:
            prompt = extract_field_prompt(payload.message, current_field, idea)
            extraction = provider._gemini_json(prompt)
        else:
            extraction = fixture_extract(current_field)

        extracted_value = extraction.get("value", payload.message)
        confidence = extraction.get("confidence", 0.7)

        # Save as intake answer
        answers = scenario.state["inputs"].get("intake_answers", [])
        # Remove existing answer for this field if any
        answers = [a for a in answers if a.get("question_id") != current_field]
        answers.append({
            "question_id": current_field,
            "answer_type": "text",
            "value": extracted_value,
            "meta": {"source_type": "inference", "confidence": confidence, "sources": []},
        })
        scenario.state["inputs"]["intake_answers"] = answers
        collected.add(current_field)

    readiness = compute_readiness(collected)

    # Generate next question
    raw_context = scenario.state["inputs"].get("raw_context")
    nf = next_field(collected)
    if nf:
        if provider.config.use_real_providers:
            prompt = next_question_prompt(idea, constraints, history, collected, raw_context=raw_context)
            ai_response = provider._gemini_json(prompt)
        else:
            ai_response = fixture_chat_response(collected) or {
                "message": "All questions answered!",
                "field": None,
                "suggestions": [],
            }

        ai_msg = ai_response.get("message", "")
        field_being_asked = ai_response.get("field", nf)
        suggestions = ai_response.get("suggestions", [])
    else:
        ai_msg = "All set! I have everything I need to build your GTM plan."
        field_being_asked = None
        suggestions = []

    # Record AI response
    history.append({
        "role": "assistant",
        "content": ai_msg,
        "field": field_being_asked or "",
        "suggestions": suggestions,
    })

    # Persist state
    scenario.state["inputs"]["chat_history"] = history
    scenario.state["meta"]["updated_at"] = store.now().isoformat()
    _commit_state(scenario, scenario.state["meta"].get("run_id", "unset"))

    return {
        "message": ai_msg,
        "field_being_asked": field_being_asked,
        "suggestions": suggestions,
        "readiness": readiness,
        "ready": readiness >= 1.0,
        "collected_fields": sorted(collected),
    }


@app.post("/scenarios/{scenario_id}/runs", response_model=RunResponse)
async def start_run(
    scenario_id: str,
    background_tasks: BackgroundTasks,
    payload: RunStartRequest | None = None,
) -> RunResponse:
    scenario = _get_scenario(scenario_id)
    request = payload or RunStartRequest()

    if not request.changed_decision:
        missing = _missing_required_intake_fields(scenario.state)
        if missing:
            scenario.state["inputs"]["open_questions"] = [
                {
                    "field": field,
                    "question": f"Please provide {field.replace('_', ' ')}",
                    "blocking": True,
                }
                for field in missing
            ]
            _commit_state(scenario, run_id=scenario.state["meta"].get("run_id", "unset"))
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "Run blocked by intake validation",
                    "missing_requirements": missing,
                },
            )

    run = store.create_run(scenario_id, changed_decision=request.changed_decision)
    scenario.state["meta"]["run_id"] = run.id
    scenario.state["meta"]["updated_at"] = store.now().isoformat()
    _commit_state(scenario, run.id)

    background_tasks.add_task(
        _execute_run,
        scenario,
        run,
        changed_decision=request.changed_decision,
        start_index=run.checkpoint_index,
        resumed=False,
        simulate_failure_at_agent=request.simulate_failure_at_agent,
    )

    return RunResponse(
        run_id=run.id,
        scenario_id=scenario_id,
        status="running",
        stream_url=f"/runs/{run.id}/stream",
    )


@app.post("/runs/{run_id}/resume", response_model=RunResponse)
async def resume_run(run_id: str, background_tasks: BackgroundTasks) -> RunResponse:
    prior_run = store.runs.get(run_id)
    if not prior_run:
        raise HTTPException(status_code=404, detail="run not found")
    if prior_run.status != "failed":
        raise HTTPException(status_code=409, detail="run is not in failed state")

    scenario = _get_scenario(prior_run.scenario_id)
    snapshot = store.latest_snapshot_for_run(run_id)
    if snapshot:
        scenario.state = deepcopy(snapshot.state_jsonb)

    resumed_run = store.create_run(
        scenario.id,
        resumed_from_run_id=prior_run.id,
        changed_decision=prior_run.changed_decision,
        checkpoint_index=prior_run.checkpoint_index,
    )

    scenario.state["meta"]["run_id"] = resumed_run.id
    scenario.state["meta"]["updated_at"] = store.now().isoformat()
    _commit_state(scenario, resumed_run.id)

    background_tasks.add_task(
        _execute_run,
        scenario,
        resumed_run,
        changed_decision=resumed_run.changed_decision,
        start_index=resumed_run.checkpoint_index,
        resumed=True,
    )

    return RunResponse(
        run_id=resumed_run.id,
        scenario_id=scenario.id,
        status="running",
        stream_url=f"/runs/{resumed_run.id}/stream",
    )


@app.post("/scenarios/{scenario_id}/decisions/{decision_key}/select")
async def select_decision(scenario_id: str, decision_key: str, payload: DecisionSelectRequest) -> dict[str, Any]:
    scenario = _get_scenario(scenario_id)
    if decision_key not in DECISION_KEYS:
        raise HTTPException(status_code=404, detail="decision key not found")

    decision = scenario.state["decisions"][decision_key]

    if payload.is_custom and not (payload.justification or "").strip():
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Custom decision override requires justification.",
                "path": f"/decisions/{decision_key}/override/justification",
            },
        )

    if decision_key == "channels" and payload.primary_channels:
        if len(payload.primary_channels) > 2 and not (payload.justification or "").strip():
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "More than 2 primary channels requires override justification.",
                    "path": "/decisions/channels/primary_channels",
                },
            )

        decision["primary_channels"] = payload.primary_channels[:2]
        decision["primary"] = payload.primary_channels[0]
        decision["secondary"] = payload.primary_channels[1] if len(payload.primary_channels) > 1 else ""

        if len(payload.primary_channels) > 2:
            scenario.state["risks"]["high_risk_flags"].append(
                {
                    "rule_id": "V-CHAN-01",
                    "severity": "high",
                    "message": "Channel override accepted with justification.",
                    "paths": ["/decisions/channels/primary_channels"],
                }
            )

    if payload.is_custom:
        decision["selected_option_id"] = "custom"
        decision["custom_value"] = payload.custom_value
        decision["override"] = {"is_custom": True, "justification": payload.justification or ""}
        impacted = sorted(impacted_decisions(decision_key))
        scenario.state["risks"]["high_risk_flags"].append(
            {
                "rule_id": "OVERRIDE-IMPACT",
                "severity": "high",
                "message": f"Override on {decision_key} impacts dependent decisions.",
                "paths": [f"/decisions/{decision_key}"],
                "impacted_decisions": impacted,
            }
        )
        _decrease_dependent_confidence(scenario.state, decision_key)
    else:
        if payload.selected_option_id:
            decision["selected_option_id"] = payload.selected_option_id
        decision["override"] = {"is_custom": False, "justification": payload.justification or ""}

    scenario.state["meta"]["updated_by"] = "orchestrator"
    scenario.state["meta"]["updated_at"] = store.now().isoformat()
    _commit_state(scenario, scenario.state["meta"].get("run_id", "unset"))

    validator_result = run_validator(scenario.state)
    return {
        "scenario_id": scenario.id,
        "decision_key": decision_key,
        "decision": decision,
        "validator": validator_result,
    }


@app.patch("/scenarios/{scenario_id}/execution-track")
async def set_execution_track(scenario_id: str, payload: ExecutionTrackRequest) -> dict[str, Any]:
    scenario = _get_scenario(scenario_id)
    scenario.state["execution"]["chosen_track"] = payload.chosen_track
    scenario.state["meta"]["updated_at"] = store.now().isoformat()
    _commit_state(scenario, scenario.state["meta"].get("run_id", "unset"))
    return {
        "scenario_id": scenario_id,
        "chosen_track": payload.chosen_track,
    }


@app.get("/runs/{run_id}", response_model=RunStatusResponse)
async def get_run(run_id: str) -> RunStatusResponse:
    run = store.runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    return RunStatusResponse(
        run_id=run.id,
        scenario_id=run.scenario_id,
        status=run.status,
        started_at=run.started_at,
        completed_at=run.completed_at,
        resumed_from_run_id=run.resumed_from_run_id,
        checkpoint_index=run.checkpoint_index,
    )


@app.get("/runs/{run_id}/stream")
async def stream_run(run_id: str) -> StreamingResponse:
    if run_id not in store.runs:
        raise HTTPException(status_code=404, detail="run not found")

    async def event_generator():
        async for event in bus.subscribe(run_id):
            yield f"id: {event['event_id']}\n"
            yield f"event: {event['type']}\n"
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/scenarios/{scenario_id}/nodes")
async def get_nodes(scenario_id: str) -> dict[str, Any]:
    scenario = _get_scenario(scenario_id)
    return {
        "scenario_id": scenario_id,
        "nodes": scenario.state["graph"].get("nodes", []),
        "groups": scenario.state["graph"].get("groups", []),
    }


@app.patch("/nodes/{node_id}")
async def patch_node(node_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    scenario = _find_scenario_by_node(node_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="node not found")

    for node in scenario.state["graph"]["nodes"]:
        if node["id"] != node_id:
            continue
        node["content"].update(payload.get("content", {}))
        node["status"] = payload.get("status", node.get("status", "draft"))
        scenario.state["meta"]["updated_at"] = store.now().isoformat()
        _commit_state(scenario, scenario.state["meta"].get("run_id", "unset"))
        return {"node": node}

    raise HTTPException(status_code=404, detail="node not found")


@app.post("/nodes/{node_id}/rerun")
async def rerun_node(node_id: str) -> dict[str, Any]:
    scenario = _find_scenario_by_node(node_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="node not found")

    changed = _decision_from_node_id(node_id)
    if not changed:
        raise HTTPException(status_code=422, detail="node does not map to rerunnable decision")

    run = store.create_run(scenario.id, changed_decision=changed)
    scenario.state["meta"]["run_id"] = run.id
    scenario.state["meta"]["updated_at"] = store.now().isoformat()
    _commit_state(scenario, run.id)

    await _execute_run(scenario, run, changed_decision=changed, resumed=False)

    return {
        "node_id": node_id,
        "run_id": run.id,
        "changed_decision": changed,
        "impacted_decisions": sorted(impacted_decisions(changed)),
        "status": store.runs[run.id].status,
    }


@app.get("/nodes/{node_id}/evidence")
async def get_node_evidence(node_id: str) -> dict[str, Any]:
    scenario = _find_scenario_by_node(node_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="node not found")

    for node in scenario.state["graph"]["nodes"]:
        if node["id"] == node_id:
            source_ids = set(node.get("evidence_refs", []))
            sources = [source for source in scenario.state["evidence"]["sources"] if source["id"] in source_ids]
            return {"node_id": node_id, "evidence": sources}

    raise HTTPException(status_code=404, detail="node not found")


@app.post("/scenarios/{scenario_id}/complete")
async def complete_scenario(scenario_id: str) -> dict[str, Any]:
    scenario = _get_scenario(scenario_id)
    validator_result = run_validator(scenario.state, finalize=True, mark_complete=True)
    if validator_result["blocking"]:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Scenario completion blocked by validator",
                "contradictions": validator_result["contradictions"],
            },
        )

    scenario.state["meta"]["updated_at"] = store.now().isoformat()
    _commit_state(scenario, scenario.state["meta"].get("run_id", "unset"))
    return {
        "scenario_id": scenario_id,
        "status": "complete",
    }


@app.post("/scenarios/{scenario_id}/export")
async def export_scenario(scenario_id: str, payload: ExportRequest) -> dict[str, Any]:
    scenario = _get_scenario(scenario_id)

    validator_result = run_validator(
        scenario.state,
        export_final=payload.kind == "final",
        finalize=payload.kind == "final",
    )
    if payload.kind == "final" and validator_result["blocking"]:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Final export blocked",
                "contradictions": validator_result["contradictions"],
            },
        )

    markdown = render_markdown_export(scenario.state)
    content = markdown if payload.format == "md" else render_html_export(scenario.state, markdown)

    export = store.create_export(scenario_id, payload.kind, payload.format, content)
    return {
        "export_id": export.id,
        "scenario_id": scenario_id,
        "kind": payload.kind,
        "format": payload.format,
    }


@app.get("/exports/{export_id}")
async def get_export(export_id: str) -> dict[str, Any]:
    export = store.exports.get(export_id)
    if not export:
        raise HTTPException(status_code=404, detail="export not found")
    return {
        "id": export.id,
        "scenario_id": export.scenario_id,
        "kind": export.kind,
        "format": export.format,
        "content": export.content,
        "created_at": export.created_at,
    }


@app.post("/scenarios/compare")
async def compare_scenarios(payload: ScenarioCompareRequest) -> dict[str, Any]:
    left = _get_scenario(payload.left_scenario_id)
    right = _get_scenario(payload.right_scenario_id)

    decision_diff: dict[str, dict[str, Any]] = {}
    for key in DECISION_KEYS:
        left_selected = left.state["decisions"][key].get("selected_option_id", "")
        right_selected = right.state["decisions"][key].get("selected_option_id", "")
        if left_selected != right_selected:
            decision_diff[key] = {
                "left": left_selected,
                "right": right_selected,
            }

    confidence_delta = _avg_confidence(right.state) - _avg_confidence(left.state)
    risk_delta = len(right.state["risks"].get("contradictions", [])) - len(left.state["risks"].get("contradictions", []))

    return {
        "left_scenario_id": left.id,
        "right_scenario_id": right.id,
        "decision_diff": decision_diff,
        "confidence_delta": round(confidence_delta, 3),
        "risk_delta": risk_delta,
    }


async def _execute_run(
    scenario: Scenario,
    run: Run,
    changed_decision: str | None = None,
    start_index: int = 0,
    resumed: bool = False,
    simulate_failure_at_agent: str | None = None,
) -> None:
    async def publish(event_type: str, data: dict[str, Any]) -> None:
        await bus.publish(run.id, scenario.id, event_type, data)

    async def checkpoint(state: dict[str, Any], index: int, agent: str) -> None:
        store.runs[run.id].checkpoint_index = index + 1
        _commit_state(scenario, run.id, state=state)

    try:
        result = await run_pipeline(
            state=deepcopy(scenario.state),
            publish=publish,
            checkpoint=checkpoint,
            changed_decision=changed_decision,
            start_index=start_index,
            resumed=resumed,
            simulate_failure_at_agent=simulate_failure_at_agent,
        )
        _commit_state(scenario, run.id, state=result.state)
        status = "blocked" if result.blocking else "completed"
        store.complete_run(
            run.id,
            status,
            completed_agents=result.completed_agents,
            skipped_agents=result.skipped_agents,
            checkpoint_index=result.last_agent_index + 1,
        )
    except PipelineFailure as exc:
        _commit_state(scenario, run.id, state=exc.state)
        store.mark_run_failure(
            run.id,
            str(exc),
            checkpoint_index=exc.failed_index,
            completed_agents=exc.completed_agents,
            skipped_agents=exc.skipped_agents,
        )
        await publish(
            "run_failed",
            {
                "message": str(exc),
                "failed_agent": exc.failed_agent,
                "checkpoint_index": exc.failed_index,
            },
        )
    except Exception as exc:  # pragma: no cover
        store.mark_run_failure(run.id, str(exc), checkpoint_index=start_index, completed_agents=[], skipped_agents=[])
        await publish("run_failed", {"message": str(exc)})


def _get_scenario(scenario_id: str) -> Scenario:
    scenario = store.scenarios.get(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="scenario not found")
    return scenario


def _commit_state(scenario: Scenario, run_id: str, state: dict[str, Any] | None = None) -> None:
    if state is not None:
        scenario.state = deepcopy(state)

    try:
        validate_state(scenario.state)
    except StateValidationError as err:
        raise HTTPException(status_code=400, detail=f"invalid canonical state: {err}") from err
    store.save_snapshot(scenario.id, run_id, scenario.state)


def _missing_required_intake_fields(state: dict[str, Any]) -> list[str]:
    provided = {answer.get("question_id") for answer in state["inputs"].get("intake_answers", [])}
    return [field for field in REQUIRED_INTAKE_FIELDS if field not in provided]


def _find_scenario_by_node(node_id: str) -> Scenario | None:
    for scenario in store.scenarios.values():
        for node in scenario.state["graph"].get("nodes", []):
            if node["id"] == node_id:
                return scenario
    return None


def _decision_from_node_id(node_id: str) -> str | None:
    if node_id.startswith("market.icp"):
        return "icp"
    if node_id.startswith("pricing"):
        return "pricing"
    if node_id.startswith("channel"):
        return "channels"
    if node_id.startswith("sales"):
        return "sales_motion"
    if node_id.startswith("positioning"):
        return "positioning"
    return None


def _decrease_dependent_confidence(state: dict[str, Any], changed_decision: str) -> None:
    impacted = impacted_decisions(changed_decision)
    impacted.add(changed_decision)
    for node in state["graph"].get("nodes", []):
        dependencies = set(node.get("dependencies", []))
        if dependencies.intersection(impacted):
            node["confidence"] = max(float(node.get("confidence", 0.5)) - 0.1, 0.1)


def _avg_confidence(state: dict[str, Any]) -> float:
    nodes = state["graph"].get("nodes", [])
    if not nodes:
        return 0.0
    total = sum(float(node.get("confidence", 0.0)) for node in nodes)
    return total / len(nodes)
