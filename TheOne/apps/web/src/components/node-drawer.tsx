"use client";

import { useMemo } from "react";
import { useAppStore } from "@/lib/store";
import {
  X,
  FileText,
  HelpCircle,
  BookOpen,
  Link,
  Activity,
  Hash,
  Shield,
  Target,
  Lightbulb,
  List,
} from "lucide-react";

interface Competitor {
  name: string;
  market_position?: string;
  threat_level?: string;
  channel_footprint?: { channels_observed?: string[]; estimated_primary?: string };
  weakness_evidence?: { claim: string; source: string; relevance: string }[];
  [key: string]: unknown;
}

const FIELD_LABELS: Record<string, string> = {
  buyer_role: "Buyer Role",
  company_size: "Company Size",
  budget_owner: "Budget Owner",
  trigger_event: "Trigger Event",
  value_prop: "Value Proposition",
  price_to_test: "Test Price",
  compliance_level: "Compliance Level",
  category: "Category",
  wedge: "Market Wedge",
  metric: "Pricing Metric",
  channel: "Channel",
  motion: "Sales Motion",
  plan: "Security Plan",
  trigger: "Trigger",
  why_it_matters: "Why It Matters",
  competitors_count: "Competitors Found",
  pillar_summary: "Pillar Summary",
  team_size: "Team Size",
  budget: "Monthly Budget",
  hiring_trigger: "Hiring Trigger",
  priority: "Priority",
  owner: "Owner",
  timeline: "Timeline",
  success_metric: "Success Metric",
  description: "Description",
  selected: "Selected Option",
  alternatives_count: "Alternatives",
  secondary: "Secondary Channel",
};

// Skip these keys from the detail section (rendered separately)
const SKIP_KEYS = new Set(["summary", "rationale", "tiers", "mvp_features", "roadmap_phases", "steps", "items", "anchors", "channel_signals"]);

function humanizeKey(key: string): string {
  return FIELD_LABELS[key] || key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatValue(key: string, val: unknown): string {
  if (typeof val === "number") {
    if (key === "budget" || key === "price_to_test") return `$${val.toLocaleString()}`;
    if (key.includes("week")) return `${val} weeks`;
    return String(val);
  }
  if (typeof val === "string") {
    return val.replace(/_/g, " ");
  }
  return JSON.stringify(val);
}

export function NodeDrawer() {
  const selectedNodeId = useAppStore((s) => s.selectedNodeId);
  const nodes = useAppStore((s) => s.nodes);
  const selectNode = useAppStore((s) => s.selectNode);
  const scenarioState = useAppStore((s) => s.scenarioState);

  const node = useMemo(
    () => nodes.find((n) => n.id === selectedNodeId) ?? null,
    [nodes, selectedNodeId]
  );

  const competitors = useMemo(
    () => (scenarioState?.evidence?.competitors ?? []) as Competitor[],
    [scenarioState]
  );

  if (!node) return null;

  const confPct = Math.round(node.confidence * 100);
  const confColor = confPct >= 70 ? "text-sage" : confPct >= 40 ? "text-amber" : "text-red-500";
  const content = node.content as Record<string, unknown>;
  const summary = typeof content.summary === "string" ? content.summary : "";
  const rationale = typeof content.rationale === "string" ? content.rationale : "";
  const tiers = Array.isArray(content.tiers) ? content.tiers : [];
  const mvpFeatures = Array.isArray(content.mvp_features) ? (content.mvp_features as string[]) : [];
  const roadmapPhases = Array.isArray(content.roadmap_phases) ? (content.roadmap_phases as string[]) : [];
  const steps = Array.isArray(content.steps) ? (content.steps as string[]) : [];
  const items = Array.isArray(content.items) ? (content.items as string[]) : [];
  const anchors = Array.isArray(content.anchors) ? content.anchors : [];
  const channelSignals = Array.isArray(content.channel_signals) ? content.channel_signals : [];

  // Remaining scalar fields
  const detailEntries = Object.entries(content).filter(
    ([key, val]) => !SKIP_KEYS.has(key) && val !== "" && val !== null && val !== undefined
  );

  const showCompetitors =
    (node.pillar === "market_intelligence" || node.pillar === "customer" || node.pillar === "positioning_pricing") &&
    competitors.length > 0;

  return (
    <aside className="w-80 shrink-0 border-l sketch-divider bg-white/80 backdrop-blur-sm overflow-y-auto animate-slide-in">
      {/* Header */}
      <div className="sticky top-0 z-10 flex items-center justify-between border-b sketch-divider bg-white/90 backdrop-blur-sm px-4 py-3">
        <h3 className="text-sm font-semibold text-ink truncate pr-2">{node.title}</h3>
        <button
          onClick={() => selectNode(null)}
          className="flex h-6 w-6 items-center justify-center sketch-rounded text-graphite hover:bg-stone-100 hover:text-ink transition-colors"
        >
          <X size={16} strokeWidth={1.5} />
        </button>
      </div>

      <div className="p-4 space-y-5">
        {/* Meta badges */}
        <div className="flex flex-wrap gap-2">
          <Badge label={node.type} color="bg-stone-100 text-graphite" />
          <Badge label={node.pillar.replace(/_/g, " ")} color="bg-sage/10 text-sage" />
          <Badge
            label={node.status}
            color={
              node.status === "final"
                ? "bg-sage/10 text-sage"
                : node.status === "needs_input"
                  ? "bg-amber/10 text-amber"
                  : "bg-stone-100 text-graphite"
            }
          />
        </div>

        {/* Summary — prominent top section */}
        {summary && (
          <div className="sketch-rounded bg-stone-50 border border-stone-200 p-3">
            <p className="text-sm text-ink leading-relaxed">{summary}</p>
          </div>
        )}

        {/* Rationale callout */}
        {rationale && (
          <div className="sketch-rounded bg-sage/5 border border-sage/20 p-3">
            <p className="text-xs font-medium text-sage mb-1 flex items-center gap-1">
              <Lightbulb size={12} strokeWidth={1.5} />
              Rationale
            </p>
            <p className="text-xs text-ink leading-relaxed">{rationale}</p>
          </div>
        )}

        {/* Confidence */}
        <div>
          <p className="text-xs font-medium text-graphite mb-1.5 flex items-center gap-1">
            <Activity size={12} strokeWidth={1.5} />
            Confidence
          </p>
          <div className="flex items-center gap-3">
            <div className="flex-1 h-2 rounded-full bg-stone-100 overflow-hidden">
              <div
                className="confidence-bar h-full rounded-full"
                style={{
                  width: `${confPct}%`,
                  background: confPct >= 70 ? "#6d8a73" : confPct >= 40 ? "#d58c2f" : "#ef4444",
                }}
              />
            </div>
            <span className={`text-sm font-bold ${confColor}`}>{confPct}%</span>
          </div>
        </div>

        {/* Pricing Tiers — compact table */}
        {tiers.length > 0 && (
          <div>
            <p className="text-xs font-medium text-graphite mb-1.5 flex items-center gap-1">
              <List size={12} strokeWidth={1.5} />
              Pricing Tiers
            </p>
            <div className="sketch-rounded sketch-border overflow-hidden">
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-stone-50">
                    <th className="text-left px-3 py-1.5 font-medium text-graphite">Tier</th>
                    <th className="text-right px-3 py-1.5 font-medium text-graphite">Price</th>
                  </tr>
                </thead>
                <tbody>
                  {tiers.map((tier: Record<string, unknown>, i: number) => (
                    <tr key={i} className="border-t border-stone-100">
                      <td className="px-3 py-1.5 text-ink">{String(tier.name || "")}</td>
                      <td className="px-3 py-1.5 text-ink text-right font-medium">${String(tier.price || 0)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* MVP Features — bulleted list */}
        {mvpFeatures.length > 0 && (
          <div>
            <p className="text-xs font-medium text-graphite mb-1.5 flex items-center gap-1">
              <FileText size={12} strokeWidth={1.5} />
              MVP Features
            </p>
            <ul className="space-y-1">
              {mvpFeatures.map((f, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-ink">
                  <span className="text-sage mt-0.5">&#8226;</span>
                  {f}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Roadmap Phases — bulleted list */}
        {roadmapPhases.length > 0 && (
          <div>
            <p className="text-xs font-medium text-graphite mb-1.5 flex items-center gap-1">
              <FileText size={12} strokeWidth={1.5} />
              Roadmap
            </p>
            <ul className="space-y-1">
              {roadmapPhases.map((p, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-ink">
                  <span className="text-sage mt-0.5">&#8226;</span>
                  {p}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Steps — numbered list */}
        {steps.length > 0 && (
          <div>
            <p className="text-xs font-medium text-graphite mb-1.5 flex items-center gap-1">
              <List size={12} strokeWidth={1.5} />
              Steps
            </p>
            <ol className="space-y-1">
              {steps.map((s, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-ink">
                  <span className="text-sage font-medium shrink-0 w-4 text-right">{i + 1}.</span>
                  {s}
                </li>
              ))}
            </ol>
          </div>
        )}

        {/* Items — checklist */}
        {items.length > 0 && (
          <div>
            <p className="text-xs font-medium text-graphite mb-1.5 flex items-center gap-1">
              <List size={12} strokeWidth={1.5} />
              Checklist
            </p>
            <ul className="space-y-1">
              {items.map((item, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-ink">
                  <span className="text-sage mt-0.5">&#9744;</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Evidence anchors */}
        {anchors.length > 0 && (
          <div>
            <p className="text-xs font-medium text-graphite mb-1.5 flex items-center gap-1">
              <BookOpen size={12} strokeWidth={1.5} />
              Pricing Evidence
            </p>
            <div className="space-y-1.5">
              {anchors.map((a: Record<string, unknown>, i: number) => (
                <div key={i} className="sketch-rounded sketch-border bg-stone-50 p-2 text-xs">
                  <span className="font-medium text-ink">{String(a.competitor || a.name || `Source ${i + 1}`)}</span>
                  {typeof a.model === "string" && <span className="text-graphite ml-1">({a.model})</span>}
                  {(typeof a.base_price === "number" || typeof a.base_price === "string") && <span className="ml-1 font-medium text-sage">${String(a.base_price)}</span>}
                  {typeof a.source_id === "string" && (
                    <span className="ml-1 sketch-rounded bg-sage/10 px-1.5 py-0.5 text-[9px] text-sage">{a.source_id}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Channel signals */}
        {channelSignals.length > 0 && (
          <div>
            <p className="text-xs font-medium text-graphite mb-1.5 flex items-center gap-1">
              <BookOpen size={12} strokeWidth={1.5} />
              Channel Signals
            </p>
            <div className="space-y-1.5">
              {channelSignals.map((s: Record<string, unknown>, i: number) => (
                <div key={i} className="sketch-rounded sketch-border bg-stone-50 p-2 text-xs text-ink">
                  {String(s.channel || s.name || `Signal ${i + 1}`)}
                  {typeof s.strength === "string" && <span className="ml-1 text-graphite">({s.strength})</span>}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Detail fields — remaining scalar content */}
        {detailEntries.length > 0 && (
          <div>
            <p className="text-xs font-medium text-graphite mb-1.5 flex items-center gap-1">
              <FileText size={12} strokeWidth={1.5} />
              Details
            </p>
            <div className="sketch-rounded sketch-border bg-stone-50 p-3 text-xs text-ink space-y-1.5">
              {detailEntries.map(([key, val]) => {
                if (typeof val === "object" && !Array.isArray(val)) return null;
                if (Array.isArray(val)) {
                  return (
                    <div key={key}>
                      <span className="font-medium text-graphite">{humanizeKey(key)}: </span>
                      <span>{val.map(String).join(", ")}</span>
                    </div>
                  );
                }
                return (
                  <div key={key}>
                    <span className="font-medium text-graphite">{humanizeKey(key)}: </span>
                    <span>{formatValue(key, val)}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Assumptions */}
        {node.assumptions.length > 0 && (
          <div>
            <p className="text-xs font-medium text-amber mb-1.5 flex items-center gap-1">
              <HelpCircle size={12} strokeWidth={1.5} />
              Assumptions ({node.assumptions.length})
            </p>
            <ul className="space-y-1">
              {node.assumptions.map((a, i) => (
                <li
                  key={i}
                  className="flex items-start gap-2 sketch-rounded border border-amber/20 bg-amber/5 px-3 py-2 text-xs text-ink"
                >
                  <HelpCircle size={12} strokeWidth={1.5} className="mt-0.5 shrink-0 text-amber" />
                  {a}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Evidence refs */}
        {node.evidence_refs.length > 0 && (
          <div>
            <p className="text-xs font-medium text-graphite mb-1.5 flex items-center gap-1">
              <BookOpen size={12} strokeWidth={1.5} />
              Evidence Sources ({node.evidence_refs.length})
            </p>
            <div className="flex flex-wrap gap-1.5">
              {node.evidence_refs.map((ref) => (
                <span
                  key={ref}
                  className="sketch-rounded border border-sage/20 bg-sage/5 px-2 py-1 text-[10px] text-sage font-medium"
                >
                  {ref}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Competitor Intel */}
        {showCompetitors && (
          <div>
            <p className="text-xs font-medium text-graphite mb-1.5 flex items-center gap-1">
              <Target size={12} strokeWidth={1.5} />
              Competitive Intel ({competitors.length})
            </p>
            <div className="space-y-2">
              {competitors.map((comp) => (
                <div
                  key={comp.name}
                  className="sketch-rounded sketch-border bg-stone-50 p-2.5 text-xs"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-semibold text-ink">{comp.name}</span>
                    {comp.threat_level && (
                      <span
                        className={`sketch-rounded px-1.5 py-0.5 text-[9px] font-medium ${
                          comp.threat_level === "high"
                            ? "bg-red-100 text-red-600"
                            : comp.threat_level === "medium"
                              ? "bg-amber/10 text-amber"
                              : "bg-stone-100 text-graphite"
                        }`}
                      >
                        {comp.threat_level} threat
                      </span>
                    )}
                    {comp.market_position && (
                      <span className="sketch-rounded bg-stone-100 px-1.5 py-0.5 text-[9px] text-graphite font-medium">
                        {comp.market_position}
                      </span>
                    )}
                  </div>
                  {comp.channel_footprint?.estimated_primary && (
                    <p className="text-[10px] text-graphite flex items-center gap-1 mb-1">
                      <Shield size={10} strokeWidth={1.5} />
                      Primary channel: {comp.channel_footprint.estimated_primary.replace(/_/g, " ")}
                    </p>
                  )}
                  {comp.weakness_evidence && comp.weakness_evidence.length > 0 && (
                    <div className="mt-1.5 space-y-1">
                      {comp.weakness_evidence.slice(0, 2).map((w, i) => (
                        <div key={i} className="text-[10px] text-graphite pl-2 border-l-2 border-amber/30">
                          <span className="italic">&ldquo;{w.claim}&rdquo;</span>
                          <span className="text-stone-400"> — {w.source}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Dependencies */}
        {node.dependencies.length > 0 && (
          <div>
            <p className="text-xs font-medium text-graphite mb-1.5 flex items-center gap-1">
              <Link size={12} strokeWidth={1.5} />
              Dependencies
            </p>
            <div className="flex flex-wrap gap-1.5">
              {node.dependencies.map((dep) => (
                <button
                  key={dep}
                  onClick={() => selectNode(dep)}
                  className="sketch-rounded border border-stone-200 bg-white px-2 py-1 text-[10px] text-ink font-medium hover:border-sage hover:text-sage transition-colors"
                >
                  {dep}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Node ID */}
        <div className="pt-2 border-t border-stone-100">
          <p className="text-[10px] text-stone-400 font-mono flex items-center gap-1">
            <Hash size={10} strokeWidth={1.5} />
            {node.id}
          </p>
        </div>
      </div>
    </aside>
  );
}

function Badge({ label, color }: { label: string; color: string }) {
  return (
    <span className={`sketch-rounded px-2.5 py-0.5 text-[10px] font-medium capitalize ${color}`}>
      {label}
    </span>
  );
}
