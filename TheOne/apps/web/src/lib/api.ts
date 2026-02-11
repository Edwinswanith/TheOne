const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

async function apiFetch<T = unknown>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    const msg = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    throw new ApiError(res.status, msg);
  }
  return res.json() as Promise<T>;
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

/* ── Projects ──────────────────────────────────────────────── */
export interface ProjectSummary {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  scenario_ids: string[];
}

export interface CreateProjectPayload {
  project_name: string;
  idea: {
    name: string;
    one_liner: string;
    problem: string;
    target_region: string;
    category: string;
  };
  constraints: {
    team_size: number;
    timeline_weeks: number;
    budget_usd_monthly: number;
    compliance_level: string;
  };
}

export interface CreateProjectResponse {
  project: ProjectSummary;
  scenario: { id: string; name: string; created_at: string; updated_at: string };
}

export const listProjects = () => apiFetch<ProjectSummary[]>("/projects");
export const createProject = (p: CreateProjectPayload) =>
  apiFetch<CreateProjectResponse>("/projects", { method: "POST", body: JSON.stringify(p) });

/* ── Scenarios ─────────────────────────────────────────────── */
export interface ScenarioDetail {
  id: string;
  project_id: string;
  name: string;
  created_at: string;
  updated_at: string;
  state: CanonicalState;
}

export const getScenario = (id: string) => apiFetch<ScenarioDetail>(`/scenarios/${id}`);

/* ── Runs ──────────────────────────────────────────────────── */
export interface RunResponse {
  run_id: string;
  scenario_id: string;
  status: string;
  stream_url: string;
}

export const startRun = (scenarioId: string, changedDecision?: string) =>
  apiFetch<RunResponse>(`/scenarios/${scenarioId}/runs`, {
    method: "POST",
    body: JSON.stringify({ changed_decision: changedDecision || null }),
  });

export const resumeRun = (runId: string) =>
  apiFetch<RunResponse>(`/runs/${runId}/resume`, { method: "POST" });

export const getRun = (runId: string) =>
  apiFetch<{ run_id: string; status: string; checkpoint_index: number }>(`/runs/${runId}`);

/* ── Intake ────────────────────────────────────────────────── */
export const submitIntake = (scenarioId: string, answers: IntakeAnswer[]) =>
  apiFetch(`/scenarios/${scenarioId}/intake`, {
    method: "POST",
    body: JSON.stringify({ answers }),
  });

/* ── Decisions ─────────────────────────────────────────────── */
export const selectDecision = (scenarioId: string, key: string, payload: Record<string, unknown>) =>
  apiFetch(`/scenarios/${scenarioId}/decisions/${key}/select`, {
    method: "POST",
    body: JSON.stringify(payload),
  });

/* ── Nodes ─────────────────────────────────────────────────── */
export const getNodes = (scenarioId: string) =>
  apiFetch<{ nodes: GraphNode[]; groups: GraphGroup[] }>(`/scenarios/${scenarioId}/nodes`);

/* ── Export ─────────────────────────────────────────────────── */
export const setExecutionTrack = (scenarioId: string, track: string) =>
  apiFetch(`/scenarios/${scenarioId}/execution-track`, {
    method: "PATCH",
    body: JSON.stringify({ chosen_track: track }),
  });

export const exportScenario = (scenarioId: string, kind: string, format: string) =>
  apiFetch<{ export_id: string }>(`/scenarios/${scenarioId}/export`, {
    method: "POST",
    body: JSON.stringify({ kind, format }),
  });

export const getExport = (exportId: string) =>
  apiFetch<{ content: string }>(`/exports/${exportId}`);

/* ── Audio ─────────────────────────────────────────────────── */
export async function transcribeAudio(audioBlob: Blob): Promise<{ text: string }> {
  const form = new FormData();
  form.append("file", audioBlob, "recording.webm");
  const res = await fetch(`${API_BASE}/audio/transcribe`, { method: "POST", body: form });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    const msg = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    throw new ApiError(res.status, msg);
  }
  return res.json() as Promise<{ text: string }>;
}

/* ── Shared types ──────────────────────────────────────────── */
export interface IntakeAnswer {
  question_id: string;
  answer_type: "mcq" | "text" | "number" | "boolean";
  value: string;
  is_recommended?: boolean;
}

export interface GraphNode {
  id: string;
  title: string;
  type: string;
  pillar: string;
  content: Record<string, unknown>;
  assumptions: string[];
  confidence: number;
  evidence_refs: string[];
  dependencies: string[];
  status: string;
}

export interface GraphGroup {
  id: string;
  title: string;
  pillar: string;
  node_ids: string[];
}

export interface CanonicalState {
  meta: Record<string, unknown>;
  idea: { name: string; one_liner: string; problem: string; target_region: string; category: string };
  constraints: Record<string, unknown>;
  inputs: { intake_answers: IntakeAnswer[]; open_questions: { field: string; question: string; blocking: boolean }[] };
  evidence: { sources: unknown[]; competitors: unknown[]; pricing_anchors: unknown[] };
  decisions: Record<string, { selected_option_id: string; options?: unknown[]; override?: Record<string, unknown> }>;
  pillars: Record<string, { summary: string }>;
  graph: { nodes: GraphNode[]; edges: unknown[]; groups: GraphGroup[] };
  risks: { contradictions: unknown[]; missing_proof: unknown[]; high_risk_flags: unknown[] };
  execution: { chosen_track: string; next_actions: unknown[]; experiments: unknown[]; assets: unknown[] };
  telemetry: { agent_timings: { agent: string; status: string; duration_ms?: number }[] };
}
