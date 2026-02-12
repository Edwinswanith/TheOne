"use client";

import { useAppStore } from "@/lib/store";
import { CheckCircle, Activity, AlertCircle, Loader2, Shield } from "lucide-react";

const AGENT_LABELS: Record<string, string> = {
  evidence_collector: "Evidence",
  competitive_teardown_agent: "Teardown",
  icp_agent: "ICP",
  positioning_agent: "Position",
  pricing_agent: "Pricing",
  channel_agent: "Channels",
  sales_motion_agent: "Sales",
  product_strategy_agent: "Product",
  tech_feasibility_agent: "Tech",
  people_cash_agent: "People",
  execution_agent: "Exec",
  graph_builder: "Graph",
  validator_agent: "Validate",
};

const CLUSTER_LABELS: Record<string, string> = {
  market_intelligence: "Market Intel",
  customer: "Customer",
  positioning_pricing: "Position & Price",
  go_to_market: "Go-to-Market",
  product_tech: "Product & Tech",
  execution: "Execution",
};

const CLUSTER_COLORS: Record<string, string> = {
  market_intelligence: "bg-[#6d8a73]/10 border-[#6d8a73]",
  customer: "bg-[#0e8ba0]/10 border-[#0e8ba0]",
  positioning_pricing: "bg-[#8b5bad]/10 border-[#8b5bad]",
  go_to_market: "bg-[#d58c2f]/10 border-[#d58c2f]",
  product_tech: "bg-[#5b7bb4]/10 border-[#5b7bb4]",
  execution: "bg-[#c75b39]/10 border-[#c75b39]",
};

function StatusIcon({ status }: { status: string }) {
  if (status === "completed") return <CheckCircle size={12} strokeWidth={1.5} className="text-sage" />;
  if (status === "running") return <Activity size={12} strokeWidth={1.5} className="text-sage animate-pulse-dot" />;
  if (status === "failed") return <AlertCircle size={12} strokeWidth={1.5} className="text-red-400" />;
  if (status === "rerunning") return <Loader2 size={12} strokeWidth={1.5} className="text-amber-500 animate-spin" />;
  return <div className="h-2.5 w-2.5 rounded-full border-2 border-stone-300 bg-white" />;
}

function ClusterTimeline() {
  const clusterStatuses = useAppStore((s) => s.clusterStatuses);
  const orchestratorStatus = useAppStore((s) => s.orchestratorStatus);
  const orchestratorConflicts = useAppStore((s) => s.orchestratorConflicts);

  const clusters = Object.entries(clusterStatuses);
  if (clusters.length === 0) return null;

  return (
    <div className="flex flex-col gap-2">
      {/* Cluster cards */}
      <div className="flex items-start gap-2 overflow-x-auto pb-1">
        {clusters.map(([name, status]) => {
          const label = CLUSTER_LABELS[name] || name;
          const colors = CLUSTER_COLORS[name] || "bg-stone-50 border-stone-300";
          return (
            <div
              key={name}
              className={`shrink-0 rounded-lg border px-3 py-2 min-w-[120px] ${colors}`}
            >
              <div className="flex items-center gap-1.5">
                <StatusIcon status={status.status} />
                <span className="text-[10px] font-accent font-medium text-ink">{label}</span>
              </div>
              {status.status === "running" && status.totalSteps > 0 && (
                <div className="mt-1.5">
                  <div className="flex justify-between text-[8px] text-graphite mb-0.5">
                    <span>{status.currentAgent}</span>
                    <span>{status.currentStep}/{status.totalSteps}</span>
                  </div>
                  <div className="h-1 bg-stone-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-sage transition-all duration-300 rounded-full"
                      style={{ width: `${(status.currentStep / status.totalSteps) * 100}%` }}
                    />
                  </div>
                </div>
              )}
              {status.status === "completed" && (
                <div className="mt-1 text-[8px] text-sage">
                  {status.totalSteps} steps done
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Orchestrator indicator */}
      {orchestratorStatus !== "idle" && (
        <div className="flex items-center gap-2 px-2 py-1.5 bg-stone-50 rounded-lg border border-stone-200">
          <Shield size={12} strokeWidth={1.5} className={
            orchestratorStatus === "checking" ? "text-amber-500 animate-pulse" :
            orchestratorStatus === "converged" ? "text-sage" :
            orchestratorStatus === "blocked" ? "text-red-400" :
            "text-graphite"
          } />
          <span className="text-[10px] font-accent text-ink">
            {orchestratorStatus === "checking" && "Cross-referencing pillars..."}
            {orchestratorStatus === "dispatching" && `${orchestratorConflicts} conflicts found — running feedback round`}
            {orchestratorStatus === "converged" && "All pillars aligned"}
            {orchestratorStatus === "blocked" && "Pivot decision required"}
          </span>
        </div>
      )}
    </div>
  );
}

function FlatTimeline() {
  const agentStatuses = useAppStore((s) => s.agentStatuses);

  return (
    <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
      {agentStatuses.map((agent, i) => {
        const label = AGENT_LABELS[agent.name] || agent.name;
        return (
          <div
            key={agent.name}
            className="flex flex-col items-center"
            style={{ animationDelay: `${i * 40}ms` }}
          >
            <div className="flex items-center w-full">
              {i > 0 && (
                <div
                  className={`h-0.5 flex-1 transition-colors duration-500 ${
                    agent.status === "completed" || agent.status === "skipped"
                      ? "bg-sage border-dashed"
                      : agent.status === "running"
                        ? "bg-sage/40 border-dashed"
                        : "bg-stone-200 border-dashed"
                  }`}
                  style={{ borderTop: "1px dashed", borderColor: "inherit" }}
                />
              )}
              <div className="shrink-0 flex items-center justify-center h-4 w-4">
                <StatusIcon status={agent.status} />
              </div>
              {i < agentStatuses.length - 1 && (
                <div
                  className={`h-0.5 flex-1 transition-colors duration-500 ${
                    agent.status === "completed" || agent.status === "skipped"
                      ? "bg-sage"
                      : "bg-stone-200"
                  }`}
                  style={{ borderTop: "1px dashed", borderColor: "inherit" }}
                />
              )}
            </div>
            <span
              className={`mt-1 text-[9px] font-accent whitespace-nowrap ${
                agent.status === "completed"
                  ? "text-sage"
                  : agent.status === "running"
                    ? "text-ink font-semibold"
                    : agent.status === "failed"
                      ? "text-red-500"
                      : "text-stone-400"
              }`}
            >
              {label}
            </span>
            {agent.patchCount !== undefined && agent.status === "completed" && (
              <span className="text-[8px] text-graphite sketch-rounded bg-stone-50 px-1">{agent.patchCount}p</span>
            )}
          </div>
        );
      })}
    </div>
  );
}

export function RunTimeline() {
  const runStatus = useAppStore((s) => s.runStatus);
  const clusterStatuses = useAppStore((s) => s.clusterStatuses);
  const hasClusterData = Object.keys(clusterStatuses).length > 0;

  if (runStatus === "idle") return null;

  return (
    <div className="shrink-0 border-t sketch-divider bg-white/70 backdrop-blur-sm px-4 py-3">
      {hasClusterData ? <ClusterTimeline /> : <FlatTimeline />}
    </div>
  );
}
