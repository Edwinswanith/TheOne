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
} from "lucide-react";

export function NodeDrawer() {
  const selectedNodeId = useAppStore((s) => s.selectedNodeId);
  const nodes = useAppStore((s) => s.nodes);
  const selectNode = useAppStore((s) => s.selectNode);

  const node = useMemo(
    () => nodes.find((n) => n.id === selectedNodeId) ?? null,
    [nodes, selectedNodeId]
  );

  if (!node) return null;

  const confPct = Math.round(node.confidence * 100);
  const confColor = confPct >= 70 ? "text-sage" : confPct >= 40 ? "text-amber" : "text-red-500";

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

        {/* Content */}
        {Object.keys(node.content).length > 0 && (
          <div>
            <p className="text-xs font-medium text-graphite mb-1.5 flex items-center gap-1">
              <FileText size={12} strokeWidth={1.5} />
              Content
            </p>
            <div className="sketch-rounded sketch-border bg-stone-50 p-3 text-xs text-ink space-y-1">
              {Object.entries(node.content).map(([key, val]) => (
                <div key={key}>
                  <span className="font-medium text-graphite">{key}: </span>
                  <span>{typeof val === "string" ? val : JSON.stringify(val)}</span>
                </div>
              ))}
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
