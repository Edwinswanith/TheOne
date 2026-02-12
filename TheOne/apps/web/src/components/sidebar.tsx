"use client";

import { useAppStore } from "@/lib/store";
import { useMemo } from "react";
import { ArrowLeft, TrendingUp, Box, Rocket, Users, CheckCircle, Circle, Tag, Zap } from "lucide-react";
import type { LucideIcon } from "lucide-react";

const PILLAR_META: Record<string, { icon: LucideIcon; color: string }> = {
  market_intelligence: { icon: TrendingUp, color: "bg-sage" },
  customer: { icon: Users, color: "bg-cyan-600" },
  positioning_pricing: { icon: Tag, color: "bg-violet-500" },
  go_to_market: { icon: Rocket, color: "bg-amber" },
  product_tech: { icon: Box, color: "bg-blue-500" },
  execution: { icon: Zap, color: "bg-orange-500" },
};

const PILLAR_LABELS: Record<string, string> = {
  market_intelligence: "Market Intelligence",
  customer: "Customer",
  positioning_pricing: "Positioning & Pricing",
  go_to_market: "Go-to-Market",
  product_tech: "Product & Tech",
  execution: "Execution",
};

export function Sidebar() {
  const scenarioState = useAppStore((s) => s.scenarioState);
  const nodes = useAppStore((s) => s.nodes);
  const selectNode = useAppStore((s) => s.selectNode);
  const selectedNodeId = useAppStore((s) => s.selectedNodeId);
  const setScreen = useAppStore((s) => s.setScreen);
  const setExpandedPillar = useAppStore((s) => s.setExpandedPillar);
  const expandedPillar = useAppStore((s) => s.expandedPillar);

  const grouped = useMemo(() => {
    const map: Record<string, typeof nodes> = {};
    for (const pillar of Object.keys(PILLAR_LABELS)) {
      map[pillar] = [];
    }
    for (const node of nodes) {
      if (node.type === "pillar") continue; // Skip Level 1 pillar summary nodes
      const p = node.pillar || "execution";
      if (!map[p]) map[p] = [];
      map[p].push(node);
    }
    return map;
  }, [nodes]);

  return (
    <aside className="flex w-60 shrink-0 flex-col border-r sketch-divider bg-white/60 backdrop-blur-sm">
      {/* Logo / back */}
      <div className="flex items-center gap-2 border-b sketch-divider px-4 py-3">
        <button
          onClick={() => setScreen("home")}
          className="text-graphite hover:text-ink transition-colors"
          title="Back to projects"
        >
          <ArrowLeft size={16} strokeWidth={1.5} />
        </button>
        <h2 className="text-lg font-accent font-bold text-ink tracking-tight">GTMGraph</h2>
      </div>

      {/* Idea summary */}
      {scenarioState && (
        <div className="border-b sketch-divider px-4 py-3">
          <p className="text-sm font-semibold text-ink truncate">{scenarioState.idea.name}</p>
          <p className="text-xs text-graphite mt-0.5 line-clamp-2">{scenarioState.idea.one_liner}</p>
        </div>
      )}

      {/* Pillar nav */}
      <nav className="flex-1 overflow-y-auto px-2 py-3">
        {Object.entries(PILLAR_LABELS).map(([key, label]) => {
          const meta = PILLAR_META[key] || { icon: Circle, color: "bg-stone-400" };
          const Icon = meta.icon;
          const pillarNodes = grouped[key] || [];

          return (
            <div key={key} className="mb-3">
              <button
                onClick={() => setExpandedPillar(expandedPillar === key ? null : key)}
                className={`flex w-full items-center gap-2 px-2 py-1 rounded-md transition-colors ${
                  expandedPillar === key ? "bg-stone-100" : "hover:bg-stone-50"
                }`}
              >
                <span
                  className={`flex h-6 w-6 items-center justify-center sketch-rounded text-white ${meta.color}`}
                >
                  <Icon size={12} strokeWidth={1.5} />
                </span>
                <span className="text-xs font-semibold text-graphite uppercase tracking-wider">
                  {label}
                </span>
                {pillarNodes.length > 0 && (
                  <span className="ml-auto text-[10px] text-graphite bg-stone-100 sketch-rounded px-1.5 py-0.5">
                    {pillarNodes.length}
                  </span>
                )}
              </button>

              {pillarNodes.map((node) => (
                <button
                  key={node.id}
                  onClick={() => selectNode(node.id === selectedNodeId ? null : node.id)}
                  className={`mt-0.5 flex w-full items-center gap-2 sketch-rounded px-2 py-1.5 text-left text-xs transition-colors ${
                    node.id === selectedNodeId
                      ? "bg-sage/10 text-sage font-medium border-l-2 border-dashed border-sage"
                      : "text-ink hover:bg-stone-100"
                  }`}
                >
                  <ConfidenceDot confidence={node.confidence} />
                  <span className="truncate">{node.title}</span>
                </button>
              ))}

              {pillarNodes.length === 0 && (
                <p className="px-2 py-1 text-[10px] text-stone-400 italic font-accent">
                  No nodes yet
                </p>
              )}
            </div>
          );
        })}
      </nav>

      {/* Decisions summary */}
      {scenarioState && (
        <div className="border-t sketch-divider px-4 py-3">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-graphite mb-2">Decisions</p>
          {["icp", "positioning", "pricing", "channels", "sales_motion"].map((key) => {
            const d = scenarioState.decisions[key];
            const selected = d?.selected_option_id;
            return (
              <div key={key} className="flex items-center gap-2 mb-1">
                {selected ? (
                  <CheckCircle size={10} strokeWidth={1.5} className="text-sage shrink-0" />
                ) : (
                  <Circle size={10} strokeWidth={1.5} className="text-stone-300 shrink-0" />
                )}
                <span className="text-[11px] text-ink capitalize">{key.replace(/_/g, " ")}</span>
                {selected && (
                  <span className="ml-auto text-[10px] text-sage font-medium truncate max-w-[80px]">
                    {selected === "custom" ? "Custom" : selected.slice(0, 12)}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      )}
    </aside>
  );
}

function ConfidenceDot({ confidence }: { confidence: number }) {
  const color =
    confidence >= 0.7 ? "bg-sage" : confidence >= 0.4 ? "bg-amber" : "bg-red-400";
  return <span className={`h-2 w-2 shrink-0 rounded-full ${color}`} />;
}
