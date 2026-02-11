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
  | "run_resumed";

export interface RunEvent {
  event_id: string;
  run_id: string;
  scenario_id: string;
  ts: string;
  type: RunEventType;
  data: Record<string, unknown>;
}
