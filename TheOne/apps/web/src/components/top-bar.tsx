"use client";

import { useAppStore } from "@/lib/store";
import {
  Play,
  RefreshCw,
  Activity,
  CheckCircle,
  AlertCircle,
  LayoutGrid,
  AlertTriangle,
  GitBranch,
} from "lucide-react";

const STATUS_STYLES: Record<string, string> = {
  idle: "bg-stone-100 text-graphite",
  starting: "bg-amber/10 text-amber",
  running: "bg-sage/10 text-sage animate-pulse-dot",
  completed: "bg-sage/10 text-sage",
  blocked: "bg-amber/10 text-amber",
  failed: "bg-red-50 text-red-600",
};

const STATUS_ICONS: Record<string, typeof Activity> = {
  running: Activity,
  starting: Activity,
  completed: CheckCircle,
  blocked: AlertCircle,
  failed: AlertCircle,
};

export function TopBar() {
  const scenarioState = useAppStore((s) => s.scenarioState);
  const runStatus = useAppStore((s) => s.runStatus);
  const startRun = useAppStore((s) => s.startRun);
  const resumeRun = useAppStore((s) => s.resumeRun);
  const setScreen = useAppStore((s) => s.setScreen);
  const nodes = useAppStore((s) => s.nodes);
  const error = useAppStore((s) => s.error);
  const clearError = useAppStore((s) => s.clearError);

  const nodeCount = nodes.length;
  const risks = scenarioState?.risks?.contradictions?.length ?? 0;
  const track = scenarioState?.execution?.chosen_track ?? "unset";

  const StatusIcon = STATUS_ICONS[runStatus];

  const REQUIRED_INTAKE = [
    "buyer_role", "company_type", "trigger_event",
    "current_workaround", "measurable_outcome",
  ];
  const intakeComplete = REQUIRED_INTAKE.every((id) =>
    scenarioState?.inputs?.intake_answers?.find(
      (a) => a.question_id === id && a.value.trim() !== ""
    )
  );

  function handleRun() {
    if (!intakeComplete) {
      setScreen("chat");
      return;
    }
    startRun();
  }

  return (
    <header className="flex items-center gap-3 border-b sketch-divider bg-white/70 backdrop-blur-sm px-4 py-2.5">
      {/* Run controls */}
      <div className="flex items-center gap-2">
        {runStatus === "idle" || runStatus === "completed" || runStatus === "blocked" ? (
          <button
            onClick={handleRun}
            className="flex items-center gap-1.5 sketch-rounded bg-sage px-4 py-1.5 text-sm font-semibold text-white shadow-sm transition-all hover:bg-ink hover:shadow-md"
          >
            <Play size={14} strokeWidth={1.5} />
            {runStatus === "idle" ? "Run Pipeline" : "Re-run"}
          </button>
        ) : runStatus === "failed" ? (
          <button
            onClick={resumeRun}
            className="flex items-center gap-1.5 sketch-rounded bg-amber px-4 py-1.5 text-sm font-semibold text-white shadow-sm transition-all hover:bg-ink"
          >
            <RefreshCw size={14} strokeWidth={1.5} />
            Resume
          </button>
        ) : (
          <span className="text-sm text-graphite flex items-center gap-1.5">
            <Activity size={14} strokeWidth={1.5} className="animate-pulse-dot" />
            Running...
          </span>
        )}

        <span
          className={`flex items-center gap-1 sketch-rounded px-2.5 py-0.5 text-[11px] font-medium capitalize ${
            STATUS_STYLES[runStatus] || STATUS_STYLES.idle
          }`}
        >
          {StatusIcon && <StatusIcon size={10} strokeWidth={1.5} />}
          {runStatus}
        </span>
      </div>

      {/* Stats */}
      <div className="ml-auto flex items-center gap-4 text-xs text-graphite">
        <span className="flex items-center gap-1">
          <LayoutGrid size={12} strokeWidth={1.5} />
          <strong className="text-ink">{nodeCount}</strong> nodes
        </span>
        {risks > 0 && (
          <span className="flex items-center gap-1 text-amber font-medium">
            <AlertTriangle size={12} strokeWidth={1.5} />
            {risks} risk{risks > 1 ? "s" : ""}
          </span>
        )}
        <span className="flex items-center gap-1 capitalize">
          <GitBranch size={12} strokeWidth={1.5} />
          Track: <strong className="text-ink">{track.replace(/_/g, " ")}</strong>
        </span>
      </div>

      {/* Error toast */}
      {error && (
        <div className="absolute top-14 right-4 z-50 max-w-sm sketch-rounded sketch-border bg-red-50 px-4 py-2.5 text-sm text-red-700 shadow-lg animate-slide-in flex items-start gap-2">
          <AlertCircle size={16} strokeWidth={1.5} className="shrink-0 mt-0.5" />
          <div>
            {error}
            <button onClick={clearError} className="ml-2 font-medium underline">
              Dismiss
            </button>
          </div>
        </div>
      )}
    </header>
  );
}
