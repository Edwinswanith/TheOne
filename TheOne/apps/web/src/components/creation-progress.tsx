"use client";

import { useAppStore } from "@/lib/store";
import { Loader2, CheckCircle, Activity, Shield } from "lucide-react";
import type { ClusterStatus } from "@/lib/types";

const PILLAR_META: Record<string, { label: string; color: string; bg: string }> = {
  market_intelligence: { label: "Market Intel", color: "#6d8a73", bg: "bg-[#6d8a73]/10" },
  customer: { label: "Customer", color: "#0e8ba0", bg: "bg-[#0e8ba0]/10" },
  positioning_pricing: { label: "Position & Price", color: "#8b5bad", bg: "bg-[#8b5bad]/10" },
  go_to_market: { label: "Go-to-Market", color: "#d58c2f", bg: "bg-[#d58c2f]/10" },
  product_tech: { label: "Product & Tech", color: "#5b7bb4", bg: "bg-[#5b7bb4]/10" },
  execution: { label: "Execution", color: "#c75b39", bg: "bg-[#c75b39]/10" },
};

const PILLAR_ORDER = [
  "market_intelligence",
  "customer",
  "positioning_pricing",
  "go_to_market",
  "product_tech",
  "execution",
];

function PillarCard({ name, status }: { name: string; status?: ClusterStatus }) {
  const meta = PILLAR_META[name] || { label: name, color: "#888", bg: "bg-stone-100" };
  const st = status?.status ?? "pending";
  const progress = status && status.totalSteps > 0
    ? Math.round((status.currentStep / status.totalSteps) * 100)
    : 0;

  return (
    <div
      className={`sketch-rounded border px-3 py-2.5 min-w-[140px] transition-all ${meta.bg}`}
      style={{ borderColor: st === "running" ? meta.color : st === "completed" ? meta.color : "#d4cfc2" }}
    >
      <div className="flex items-center gap-1.5 mb-1.5">
        {st === "completed" ? (
          <CheckCircle size={12} strokeWidth={1.5} style={{ color: meta.color }} />
        ) : st === "running" ? (
          <Activity size={12} strokeWidth={1.5} className="animate-pulse" style={{ color: meta.color }} />
        ) : (
          <div className="h-2.5 w-2.5 rounded-full border-2 border-stone-300 bg-white" />
        )}
        <span className="text-[11px] font-medium text-ink">{meta.label}</span>
      </div>

      {st === "running" && status && status.totalSteps > 0 && (
        <div>
          <div className="flex justify-between text-[8px] text-graphite mb-0.5">
            <span className="truncate max-w-[90px]">{status.currentAgent?.replace(/_/g, " ")}</span>
            <span>{status.currentStep}/{status.totalSteps}</span>
          </div>
          <div className="h-1 bg-white/60 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-300"
              style={{ width: `${progress}%`, background: meta.color }}
            />
          </div>
        </div>
      )}
      {st === "completed" && (
        <p className="text-[9px]" style={{ color: meta.color }}>
          {status?.totalSteps ?? 0} steps done
        </p>
      )}
    </div>
  );
}

export function CreationProgress() {
  const progress = useAppStore((s) => s.creationProgress);
  const runStatus = useAppStore((s) => s.runStatus);
  const clusterStatuses = useAppStore((s) => s.clusterStatuses);
  const orchestratorStatus = useAppStore((s) => s.orchestratorStatus);
  const orchestratorConflicts = useAppStore((s) => s.orchestratorConflicts);

  const hasClusterData = Object.keys(clusterStatuses).length > 0;

  // During project creation (no run yet), show simple progress
  if (!hasClusterData && runStatus === "idle") {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-[#faf8f3]">
        <div className="text-center space-y-6">
          <Loader2
            size={32}
            strokeWidth={1.5}
            className="mx-auto animate-spin text-sage"
          />
          <p
            key={progress}
            className="text-lg font-medium text-ink animate-fade-in"
          >
            {progress}
          </p>
          <p className="text-xs text-graphite">
            This usually takes a few seconds
          </p>
        </div>
      </div>
    );
  }

  // During cluster pipeline run, show pillar cards
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-[#faf8f3]">
      <div className="max-w-lg w-full px-6 space-y-6">
        <div className="text-center">
          <Loader2
            size={28}
            strokeWidth={1.5}
            className="mx-auto animate-spin text-sage mb-3"
          />
          <p className="text-lg font-medium text-ink">
            {runStatus === "starting" ? "Starting pipeline..." : "Analyzing your idea..."}
          </p>
          <p className="text-xs text-graphite mt-1">
            6 analysis clusters running in parallel
          </p>
        </div>

        {/* Pillar cards in 2x3 grid */}
        <div className="grid grid-cols-3 gap-2.5">
          {PILLAR_ORDER.map((name) => (
            <PillarCard key={name} name={name} status={clusterStatuses[name]} />
          ))}
        </div>

        {/* Orchestrator status */}
        {orchestratorStatus !== "idle" && (
          <div className="flex items-center justify-center gap-2 px-3 py-2 bg-white/70 sketch-rounded border border-stone-200">
            <Shield size={14} strokeWidth={1.5} className={
              orchestratorStatus === "checking" ? "text-amber-500 animate-pulse" :
              orchestratorStatus === "converged" ? "text-sage" :
              orchestratorStatus === "blocked" ? "text-red-400" :
              "text-graphite"
            } />
            <span className="text-[11px] font-medium text-ink">
              {orchestratorStatus === "checking" && "Cross-referencing pillars..."}
              {orchestratorStatus === "dispatching" && `${orchestratorConflicts} conflicts found — running feedback round`}
              {orchestratorStatus === "converged" && "All pillars aligned"}
              {orchestratorStatus === "blocked" && "Pivot decision required"}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
