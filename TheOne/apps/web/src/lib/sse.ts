import type { RunEvent, RunEventType } from "@/lib/types";

const EVENT_TYPES: RunEventType[] = [
  "run_started",
  "agent_started",
  "agent_progress",
  "agent_completed",
  "state_checkpointed",
  "node_created",
  "node_updated",
  "validator_warning",
  "run_blocked",
  "run_completed",
  "run_failed",
  "run_resumed",
  // Cluster pipeline events
  "cluster_phase_started",
  "cluster_started",
  "cluster_completed",
  "sub_agent_started",
  "sub_agent_completed",
  "sub_agent_reasoning_step",
  "orchestrator_started",
  "orchestrator_completed",
  "feedback_round_started",
  "feedback_round_completed",
  "convergence_check",
  "pivot_decision_required",
];

export function subscribeToRun(runId: string, onEvent: (event: RunEvent) => void) {
  const url = `${process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000"}/runs/${runId}/stream`;
  const source = new EventSource(url);

  const handler = (e: MessageEvent) => {
    const event = JSON.parse(e.data) as RunEvent;
    onEvent(event);
  };

  for (const t of EVENT_TYPES) {
    source.addEventListener(t, handler);
  }

  source.onerror = () => {
    source.close();
  };

  return () => {
    for (const t of EVENT_TYPES) {
      source.removeEventListener(t, handler);
    }
    source.close();
  };
}
