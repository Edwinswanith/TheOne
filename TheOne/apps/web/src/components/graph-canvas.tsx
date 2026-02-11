"use client";

import { useCallback, useMemo } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  useNodesState,
  useEdgesState,
  NodeTypes,
  Handle,
  Position,
} from "reactflow";
import "reactflow/dist/style.css";
import { useAppStore } from "@/lib/store";
import type { GraphNode as GNode } from "@/lib/api";
import {
  GitBranch,
  FileSearch,
  ClipboardList,
  FileText,
  FlaskConical,
  AlertTriangle,
  CheckSquare,
  LayoutGrid,
  HelpCircle,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

const PILLAR_COLORS: Record<string, { bg: string; border: string; header: string }> = {
  market_to_money: { bg: "#e8f0ea", border: "#6d8a73", header: "#6d8a73" },
  product: { bg: "#e8ecf4", border: "#5b7bb4", header: "#5b7bb4" },
  execution: { bg: "#fef3e2", border: "#d58c2f", header: "#d58c2f" },
  people_and_cash: { bg: "#f0e8f4", border: "#8b5bad", header: "#8b5bad" },
};

const TYPE_ICONS: Record<string, LucideIcon> = {
  decision: GitBranch,
  evidence: FileSearch,
  plan: ClipboardList,
  asset: FileText,
  experiment: FlaskConical,
  risk: AlertTriangle,
  checklist: CheckSquare,
};

/* Custom node component */
function GtmNode({ data }: { data: GNode & { isSelected: boolean } }) {
  const pillar = PILLAR_COLORS[data.pillar] || PILLAR_COLORS.execution;
  const Icon = TYPE_ICONS[data.type] || HelpCircle;
  const confPct = Math.round(data.confidence * 100);

  return (
    <div
      className="sketch-rounded bg-white shadow-sm transition-shadow hover:shadow-md"
      style={{
        border: `2px solid ${data.isSelected ? pillar.border : "#d4cfc2"}`,
        boxShadow: data.isSelected
          ? `1px 2px 0 0 rgba(0,0,0,0.03), 0 4px 16px rgba(0,0,0,0.08)`
          : `1px 1px 0 0 rgba(0,0,0,0.02), 0 2px 8px rgba(0,0,0,0.04)`,
        minWidth: 180,
        maxWidth: 240,
      }}
    >
      <Handle type="target" position={Position.Top} className="!bg-stone-400 !w-2 !h-2" />

      {/* Header */}
      <div
        className="flex items-center gap-2 px-3 py-1.5"
        style={{
          background: pillar.bg,
          borderRadius: "10px 6px 0 0",
        }}
      >
        <span
          className="flex h-5 w-5 items-center justify-center sketch-rounded text-white"
          style={{ background: pillar.header }}
        >
          <Icon size={10} strokeWidth={1.5} />
        </span>
        <span className="text-xs font-semibold text-ink truncate">{data.title}</span>
      </div>

      {/* Body */}
      <div className="px-3 py-2">
        {/* Confidence bar */}
        <div className="flex items-center gap-2 mb-1">
          <div className="flex-1 h-1.5 rounded-full bg-stone-100 overflow-hidden">
            <div
              className="confidence-bar h-full rounded-full"
              style={{
                width: `${confPct}%`,
                background: confPct >= 70 ? "#6d8a73" : confPct >= 40 ? "#d58c2f" : "#ef4444",
              }}
            />
          </div>
          <span className="text-[10px] text-graphite font-medium">{confPct}%</span>
        </div>

        {/* Status badge */}
        <span
          className={`inline-block sketch-rounded px-2 py-0.5 text-[9px] font-medium ${
            data.status === "final"
              ? "bg-sage/10 text-sage"
              : data.status === "needs_input"
                ? "bg-amber/10 text-amber"
                : "bg-stone-100 text-graphite"
          }`}
        >
          {data.status}
        </span>

        {data.assumptions.length > 0 && (
          <span className="ml-1 text-[9px] text-amber">
            {data.assumptions.length} assumption{data.assumptions.length > 1 ? "s" : ""}
          </span>
        )}
      </div>

      <Handle type="source" position={Position.Bottom} className="!bg-stone-400 !w-2 !h-2" />
    </div>
  );
}

const nodeTypes: NodeTypes = { gtmNode: GtmNode };

export function GraphCanvas() {
  const storeNodes = useAppStore((s) => s.nodes);
  const scenarioState = useAppStore((s) => s.scenarioState);
  const selectNode = useAppStore((s) => s.selectNode);
  const selectedNodeId = useAppStore((s) => s.selectedNodeId);

  /* Convert store nodes → React Flow nodes with grid layout */
  const { rfNodes, rfEdges } = useMemo(() => {
    const pillarOrder = ["market_to_money", "product", "execution", "people_and_cash"];
    const groups: Record<string, GNode[]> = {};
    pillarOrder.forEach((p) => (groups[p] = []));

    for (const node of storeNodes) {
      const p = node.pillar || "execution";
      if (!groups[p]) groups[p] = [];
      groups[p].push(node);
    }

    const rfNodes: Node[] = [];
    let colX = 40;

    for (const pillar of pillarOrder) {
      const pillarNodes = groups[pillar] || [];
      let rowY = 40;

      for (const node of pillarNodes) {
        rfNodes.push({
          id: node.id,
          type: "gtmNode",
          position: { x: colX, y: rowY },
          data: { ...node, isSelected: node.id === selectedNodeId },
        });
        rowY += 140;
      }
      colX += 280;
    }

    /* Edges from dependencies */
    const rfEdges: Edge[] = [];
    const edges = scenarioState?.graph?.edges ?? [];
    for (const edge of edges as { id: string; source: string; target: string; type: string }[]) {
      rfEdges.push({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        type: "smoothstep",
        animated: edge.type === "blocks",
        style: { stroke: "#c4b89a", strokeWidth: 1.5 },
      });
    }

    /* Also create edges from node.dependencies */
    for (const node of storeNodes) {
      for (const dep of node.dependencies) {
        const edgeId = `dep-${dep}-${node.id}`;
        if (!rfEdges.find((e) => e.id === edgeId)) {
          rfEdges.push({
            id: edgeId,
            source: dep,
            target: node.id,
            type: "smoothstep",
            style: { stroke: "#d4cfc2", strokeWidth: 1, strokeDasharray: "6 3" },
          });
        }
      }
    }

    return { rfNodes, rfEdges };
  }, [storeNodes, scenarioState, selectedNodeId]);

  const [flowNodes, , onNodesChange] = useNodesState(rfNodes);
  const [flowEdges, , onEdgesChange] = useEdgesState(rfEdges);

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => selectNode(node.id),
    [selectNode]
  );

  if (storeNodes.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center bg-[#faf8f3]">
        <div className="text-center animate-fade-in">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center sketch-rounded bg-sage/10">
            <LayoutGrid size={32} strokeWidth={1.5} className="text-sage" />
          </div>
          <h3 className="text-lg font-semibold text-ink font-accent text-2xl">No graph nodes yet</h3>
          <p className="mt-1 text-sm text-graphite max-w-xs mx-auto">
            Click <span className="sketch-underline font-medium">&ldquo;Run Pipeline&rdquo;</span> to generate evidence-backed nodes across all 4 pillars.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 bg-[#faf8f3]">
      <ReactFlow
        nodes={flowNodes}
        edges={flowEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        minZoom={0.3}
        maxZoom={2}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#ddd8cc" gap={24} size={1} />
        <Controls className="!bg-white/80 !border-stone-200 !shadow-card !rounded-sketch" />
        <MiniMap
          nodeStrokeWidth={2}
          className="!bg-white/80 !border-stone-200"
          maskColor="rgba(247,242,232,0.7)"
        />
      </ReactFlow>
    </div>
  );
}
