"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  NodeTypes,
  Handle,
  Position,
  NodeChange,
  EdgeChange,
  applyNodeChanges,
  applyEdgeChanges,
  useReactFlow,
  ReactFlowProvider,
} from "reactflow";
import dagre from "dagre";
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
  ArrowLeft,
  ChevronRight,
  CheckCircle,
  Activity,
  Loader2,
  Shield,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { ClusterStatus } from "@/lib/types";

const PILLAR_COLORS: Record<string, { bg: string; border: string; header: string }> = {
  market_intelligence: { bg: "#e8f0ea", border: "#6d8a73", header: "#6d8a73" },
  customer: { bg: "#dff0f7", border: "#0e8ba0", header: "#0e8ba0" },
  positioning_pricing: { bg: "#ede8f4", border: "#8b5bad", header: "#8b5bad" },
  go_to_market: { bg: "#fef3e2", border: "#d58c2f", header: "#d58c2f" },
  product_tech: { bg: "#e8ecf4", border: "#5b7bb4", header: "#5b7bb4" },
  execution: { bg: "#fcece8", border: "#c75b39", header: "#c75b39" },
};

const PILLAR_LABELS: Record<string, string> = {
  market_intelligence: "Market Intelligence",
  customer: "Customer",
  positioning_pricing: "Positioning & Pricing",
  go_to_market: "Go-to-Market",
  product_tech: "Product & Tech",
  execution: "Execution",
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

/* Map decision keys used in dependencies to actual node IDs */
const DEP_KEY_TO_NODE_ID: Record<string, string> = {
  icp: "market.icp.summary",
  positioning: "positioning.wedge",
  pricing: "pricing.metric",
  channels: "channel.primary",
  sales_motion: "sales.motion",
  product: "product.core_offer",
  tech: "product.security_plan",
  execution: "execution.validation_sprint",
  people_and_cash: "people.team_plan",
};

const NODE_WIDTH = 220;
const NODE_HEIGHT = 100;
const PILLAR_NODE_WIDTH = 280;
const PILLAR_NODE_HEIGHT = 110;

/* dagre auto-layout */
function getLayoutedElements(nodes: Node[], edges: Edge[], isPillarView: boolean) {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({
    rankdir: isPillarView ? "LR" : "TB",
    nodesep: isPillarView ? 80 : 60,
    ranksep: isPillarView ? 120 : 100,
    marginx: 40,
    marginy: 40,
  });

  nodes.forEach((node) => {
    const isPillar = node.type === "pillarNode";
    g.setNode(node.id, {
      width: isPillar ? PILLAR_NODE_WIDTH : NODE_WIDTH,
      height: isPillar ? PILLAR_NODE_HEIGHT : NODE_HEIGHT,
    });
  });

  edges.forEach((edge) => {
    g.setEdge(edge.source, edge.target);
  });

  dagre.layout(g);

  const layoutedNodes = nodes.map((node) => {
    const isPillar = node.type === "pillarNode";
    const w = isPillar ? PILLAR_NODE_WIDTH : NODE_WIDTH;
    const h = isPillar ? PILLAR_NODE_HEIGHT : NODE_HEIGHT;
    const pos = g.node(node.id);
    return {
      ...node,
      position: {
        x: pos.x - w / 2,
        y: pos.y - h / 2,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
}

function ClusterStatusIcon({ status }: { status: string }) {
  if (status === "completed") return <CheckCircle size={12} strokeWidth={1.5} className="text-sage" />;
  if (status === "running") return <Activity size={12} strokeWidth={1.5} className="text-sage animate-pulse" />;
  if (status === "rerunning") return <Loader2 size={12} strokeWidth={1.5} className="text-amber-500 animate-spin" />;
  if (status === "invalidated") return <AlertTriangle size={12} strokeWidth={1.5} className="text-red-400" />;
  return <div className="h-2.5 w-2.5 rounded-full border-2 border-stone-300 bg-white" />;
}

/* Level 1 pillar card node */
function PillarNode({ data }: { data: { pillar: string; title: string; childCount: number; avgConfidence: number; clusterStatus?: ClusterStatus } }) {
  const colors = PILLAR_COLORS[data.pillar] || PILLAR_COLORS.execution;
  const confPct = Math.round(data.avgConfidence * 100);
  const cs = data.clusterStatus;

  return (
    <div
      className="sketch-rounded bg-white shadow-md hover:shadow-lg transition-shadow cursor-pointer"
      style={{
        border: `2px solid ${colors.border}`,
        width: PILLAR_NODE_WIDTH,
        minHeight: PILLAR_NODE_HEIGHT,
      }}
    >
      {/* Colored header bar */}
      <div
        className="flex items-center gap-3 px-4 py-2.5"
        style={{ background: colors.bg, borderRadius: "10px 6px 0 0" }}
      >
        <span
          className="flex h-7 w-7 items-center justify-center sketch-rounded text-white"
          style={{ background: colors.header }}
        >
          <LayoutGrid size={14} strokeWidth={1.5} />
        </span>
        <span className="text-sm font-semibold text-ink">{data.title}</span>
        <div className="ml-auto flex items-center gap-1.5">
          {cs && <ClusterStatusIcon status={cs.status} />}
          <span className="text-xs text-graphite bg-white/70 sketch-rounded px-2 py-0.5">
            {data.childCount} node{data.childCount !== 1 ? "s" : ""}
          </span>
        </div>
      </div>

      {/* Body */}
      <div className="px-4 py-3">
        {/* Cluster progress bar */}
        {cs && cs.status === "running" && cs.totalSteps > 0 ? (
          <div className="mb-2">
            <div className="flex justify-between text-[9px] text-graphite mb-0.5">
              <span>{cs.currentAgent?.replace(/_/g, " ")}</span>
              <span>{cs.currentStep}/{cs.totalSteps}</span>
            </div>
            <div className="h-1.5 bg-stone-100 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-300"
                style={{
                  width: `${(cs.currentStep / cs.totalSteps) * 100}%`,
                  background: colors.header,
                }}
              />
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-2 mb-2">
            <div className="flex-1 h-2 rounded-full bg-stone-100 overflow-hidden">
              <div
                className="h-full rounded-full transition-all"
                style={{
                  width: `${confPct}%`,
                  background: confPct >= 70 ? colors.header : confPct >= 40 ? "#d58c2f" : "#ef4444",
                }}
              />
            </div>
            <span className="text-xs font-medium text-graphite">{confPct}%</span>
          </div>
        )}
        <p className="text-[10px] text-graphite flex items-center gap-1">
          {cs?.status === "completed" ? (
            <><span className="text-sage">{cs.totalSteps} steps done</span> &middot; Click to explore <ChevronRight size={10} /></>
          ) : (
            <>Click to explore <ChevronRight size={10} /></>
          )}
        </p>
      </div>
    </div>
  );
}

/* Custom node component */
function GtmNode({ data }: { data: GNode & { isSelected: boolean; isRerunning?: boolean } }) {
  const pillar = PILLAR_COLORS[data.pillar] || PILLAR_COLORS.execution;
  const Icon = TYPE_ICONS[data.type] || HelpCircle;
  const confPct = Math.round(data.confidence * 100);

  return (
    <div
      className={`sketch-rounded bg-white shadow-sm transition-shadow hover:shadow-md ${
        data.isRerunning ? "animate-pulse ring-2 ring-sage/50" : ""
      }`}
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
        {/* Status indicator */}
        <span
          className={`ml-auto h-2 w-2 rounded-full ${
            data.status === "final"
              ? "bg-sage"
              : data.status === "needs_input" || data.status === "needs-input"
                ? "bg-amber animate-pulse"
                : "bg-stone-300"
          }`}
          title={data.status}
        />
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
              : data.status === "needs_input" || data.status === "needs-input"
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

        {typeof data.content?.summary === "string" && data.content.summary && (
          <p className="text-[9px] text-graphite mt-1 line-clamp-2 leading-tight">
            {data.content.summary}
          </p>
        )}
      </div>

      <Handle type="source" position={Position.Bottom} className="!bg-stone-400 !w-2 !h-2" />
    </div>
  );
}

const nodeTypes: NodeTypes = { gtmNode: GtmNode, pillarNode: PillarNode };

function GraphCanvasInner() {
  const storeNodes = useAppStore((s) => s.nodes);
  const scenarioState = useAppStore((s) => s.scenarioState);
  const selectNode = useAppStore((s) => s.selectNode);
  const selectedNodeId = useAppStore((s) => s.selectedNodeId);
  const runStatus = useAppStore((s) => s.runStatus);
  const expandedPillar = useAppStore((s) => s.expandedPillar);
  const setExpandedPillar = useAppStore((s) => s.setExpandedPillar);
  const clusterStatuses = useAppStore((s) => s.clusterStatuses);
  const orchestratorStatus = useAppStore((s) => s.orchestratorStatus);
  const { fitView } = useReactFlow();

  /* Compute pillar stats */
  const pillarStats = useMemo(() => {
    const stats: Record<string, { count: number; totalConf: number }> = {};
    for (const n of storeNodes) {
      if (n.type === "pillar") continue;
      const s = stats[n.pillar] ?? { count: 0, totalConf: 0 };
      s.count++;
      s.totalConf += n.confidence;
      stats[n.pillar] = s;
    }
    return stats;
  }, [storeNodes]);

  const isPillarView = !expandedPillar;

  /* Convert store nodes -> React Flow nodes + edges */
  const { rfNodes, rfEdges } = useMemo(() => {
    // Filter visible nodes based on expanded state
    const visibleStoreNodes = storeNodes.filter((n) => {
      if (isPillarView) return n.type === "pillar";
      if (n.type === "pillar") return false;
      return n.pillar === expandedPillar;
    });

    const rfNodes: Node[] = visibleStoreNodes.map((node) => {
      if (node.type === "pillar") {
        const stats = pillarStats[node.pillar] ?? { count: 0, totalConf: 0 };
        return {
          id: node.id,
          type: "pillarNode",
          position: { x: 0, y: 0 },
          data: {
            pillar: node.pillar,
            title: PILLAR_LABELS[node.pillar] || node.title,
            childCount: stats.count,
            avgConfidence: stats.count > 0 ? stats.totalConf / stats.count : 0,
            clusterStatus: clusterStatuses[node.pillar] ?? undefined,
          },
        };
      }
      return {
        id: node.id,
        type: "gtmNode",
        position: { x: 0, y: 0 },
        data: {
          ...node,
          isSelected: node.id === selectedNodeId,
          isRerunning: runStatus === "starting" || runStatus === "running" ? false : undefined,
        },
      };
    });

    /* Edges — only for detail view */
    const rfEdges: Edge[] = [];
    if (!isPillarView) {
      const edges = scenarioState?.graph?.edges ?? [];
      const visibleIds = new Set(visibleStoreNodes.map((n) => n.id));

      for (const edge of edges as { id: string; source: string; target: string; type: string }[]) {
        if (visibleIds.has(edge.source) && visibleIds.has(edge.target)) {
          rfEdges.push({
            id: edge.id,
            source: edge.source,
            target: edge.target,
            type: "smoothstep",
            animated: edge.type === "blocks",
            style: { stroke: "#c4b89a", strokeWidth: 1.5 },
          });
        }
      }

      /* Edges from node.dependencies */
      for (const node of visibleStoreNodes) {
        for (const dep of node.dependencies) {
          const resolvedId = DEP_KEY_TO_NODE_ID[dep] ?? dep;
          if (!visibleIds.has(resolvedId)) continue;

          const edgeId = `dep-${resolvedId}-${node.id}`;
          if (!rfEdges.find((e) => e.id === edgeId)) {
            rfEdges.push({
              id: edgeId,
              source: resolvedId,
              target: node.id,
              type: "smoothstep",
              style: { stroke: "#d4cfc2", strokeWidth: 1, strokeDasharray: "6 3" },
            });
          }
        }
      }
    }

    /* Apply dagre layout */
    if (rfNodes.length > 0) {
      const layouted = getLayoutedElements(rfNodes, rfEdges, isPillarView);
      return { rfNodes: layouted.nodes, rfEdges: layouted.edges };
    }

    return { rfNodes, rfEdges };
  }, [storeNodes, scenarioState, selectedNodeId, runStatus, expandedPillar, isPillarView, pillarStats, clusterStatuses]);

  /* Controlled mode: sync store -> local state, allow drag interactions */
  const [localNodes, setLocalNodes] = useState<Node[]>(rfNodes);
  const [localEdges, setLocalEdges] = useState<Edge[]>(rfEdges);

  useEffect(() => {
    setLocalNodes(rfNodes);
    // Fit view after layout update
    setTimeout(() => fitView({ padding: 0.3, duration: 300 }), 50);
  }, [rfNodes, fitView]);

  useEffect(() => {
    setLocalEdges(rfEdges);
  }, [rfEdges]);

  const onNodesChange = useCallback(
    (changes: NodeChange[]) => setLocalNodes((nds) => applyNodeChanges(changes, nds)),
    []
  );

  const onEdgesChange = useCallback(
    (changes: EdgeChange[]) => setLocalEdges((eds) => applyEdgeChanges(changes, eds)),
    []
  );

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      if (node.type === "pillarNode") {
        setExpandedPillar(node.data.pillar);
      } else {
        selectNode(node.id);
      }
    },
    [selectNode, setExpandedPillar]
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
            Click <span className="sketch-underline font-medium">&ldquo;Run Pipeline&rdquo;</span> to generate evidence-backed nodes across all pillars.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 bg-[#faf8f3] relative">
      {/* Orchestrator status overlay */}
      {orchestratorStatus !== "idle" && isPillarView && (
        <div className="absolute top-3 right-3 z-10 sketch-rounded px-3 py-2 bg-white/90 backdrop-blur-sm border border-stone-200 shadow-sm flex items-center gap-2">
          <Shield size={14} strokeWidth={1.5} className={
            orchestratorStatus === "checking" ? "text-amber-500 animate-pulse" :
            orchestratorStatus === "converged" ? "text-sage" :
            orchestratorStatus === "blocked" ? "text-red-400" :
            "text-graphite"
          } />
          <span className="text-[10px] font-medium text-ink">
            {orchestratorStatus === "checking" && "Cross-referencing pillars..."}
            {orchestratorStatus === "dispatching" && "Running feedback round..."}
            {orchestratorStatus === "converged" && "All pillars aligned"}
            {orchestratorStatus === "blocked" && "Pivot decision required"}
          </span>
        </div>
      )}

      {/* Back to pillars button */}
      {expandedPillar && (
        <button
          onClick={() => setExpandedPillar(null)}
          className="absolute top-3 left-3 z-10 sketch-rounded px-3 py-1.5 bg-white/90 backdrop-blur-sm border border-stone-200 shadow-sm text-xs font-medium text-ink hover:bg-white hover:shadow-md transition-all flex items-center gap-1.5"
        >
          <ArrowLeft size={12} strokeWidth={1.5} />
          All Pillars
        </button>
      )}

      <ReactFlow
        nodes={localNodes}
        edges={localEdges}
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

export function GraphCanvas() {
  return (
    <ReactFlowProvider>
      <GraphCanvasInner />
    </ReactFlowProvider>
  );
}
