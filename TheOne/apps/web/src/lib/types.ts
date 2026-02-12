export type RunEventType =
  | "run_started"
  | "agent_started"
  | "agent_progress"
  | "agent_completed"
  | "state_checkpointed"
  | "node_created"
  | "node_updated"
  | "validator_warning"
  | "run_blocked"
  | "run_completed"
  | "run_failed"
  | "run_resumed"
  // Cluster pipeline events
  | "cluster_phase_started"
  | "cluster_started"
  | "cluster_completed"
  | "sub_agent_started"
  | "sub_agent_completed"
  | "sub_agent_reasoning_step"
  | "orchestrator_started"
  | "orchestrator_completed"
  | "feedback_round_started"
  | "feedback_round_completed"
  | "convergence_check"
  | "pivot_decision_required";

export interface RunEvent {
  event_id: string;
  run_id: string;
  scenario_id: string;
  ts: string;
  type: RunEventType;
  data: Record<string, unknown>;
}

export interface ReasoningStep {
  step: number;
  action: string;
  thought: string;
  data: Record<string, unknown> | null;
  confidence: number;
  source_ids: string[];
}

export interface ReasoningArtifact {
  artifact_id: string;
  agent: string;
  pillar: string;
  round: number;
  reasoning_chain: ReasoningStep[];
  output_summary: string;
  execution_meta: Record<string, unknown>;
}

export interface ClusterStatus {
  status: "pending" | "running" | "completed" | "rerunning" | "invalidated";
  round: number;
  currentStep: number;
  totalSteps: number;
  currentAgent: string;
  confidence: number | null;
  changeScore: number | null;
}
