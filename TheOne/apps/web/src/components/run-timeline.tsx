"use client";

import { useAppStore } from "@/lib/store";
import { CheckCircle, Activity, AlertCircle } from "lucide-react";

const AGENT_LABELS: Record<string, string> = {
  evidence_collector: "Evidence",
  icp_agent: "ICP",
  positioning_agent: "Position",
  pricing_agent: "Pricing",
  channel_strategy_agent: "Channels",
  sales_motion_agent: "Sales",
  product_strategy_agent: "Product",
  tech_architecture_agent: "Tech",
  people_cash_agent: "People",
  execution_agent: "Exec",
  graph_builder: "Graph",
  validator_agent: "Validate",
};

export function RunTimeline() {
  const agentStatuses = useAppStore((s) => s.agentStatuses);
  const runStatus = useAppStore((s) => s.runStatus);

  if (runStatus === "idle") return null;

  return (
    <div className="shrink-0 border-t sketch-divider bg-white/70 backdrop-blur-sm px-4 py-3">
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
        {agentStatuses.map((agent, i) => {
          const label = AGENT_LABELS[agent.name] || agent.name;
          return (
            <div
              key={agent.name}
              className="flex flex-col items-center"
              style={{ animationDelay: `${i * 40}ms` }}
            >
              {/* Connector line */}
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
                {/* Status icon/dot */}
                <div className="shrink-0 flex items-center justify-center h-4 w-4">
                  {agent.status === "completed" ? (
                    <CheckCircle size={12} strokeWidth={1.5} className="text-sage" />
                  ) : agent.status === "running" ? (
                    <Activity size={12} strokeWidth={1.5} className="text-sage animate-pulse-dot" />
                  ) : agent.status === "failed" ? (
                    <AlertCircle size={12} strokeWidth={1.5} className="text-red-400" />
                  ) : agent.status === "skipped" ? (
                    <div className="h-2.5 w-2.5 rounded-full bg-stone-300" />
                  ) : (
                    <div className="h-2.5 w-2.5 rounded-full border-2 border-stone-300 bg-white" />
                  )}
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
              {/* Label */}
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
    </div>
  );
}
