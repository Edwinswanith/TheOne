"use client";

import { useAppStore } from "@/lib/store";
import { Sidebar } from "@/components/sidebar";
import { TopBar } from "@/components/top-bar";
import { GraphCanvas } from "@/components/graph-canvas";
import { NodeDrawer } from "@/components/node-drawer";
import { RunTimeline } from "@/components/run-timeline";

export function WorkspaceShell() {
  const scenarioState = useAppStore((s) => s.scenarioState);
  const selectedNodeId = useAppStore((s) => s.selectedNodeId);

  if (!scenarioState) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <p className="text-graphite text-sm font-accent text-lg">Loading workspace...</p>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden animate-fade-in">
      {/* Left sidebar */}
      <Sidebar />

      {/* Main content */}
      <div className="flex flex-1 flex-col min-w-0">
        <TopBar />

        <div className="flex flex-1 overflow-hidden">
          {/* Center: Graph + Run Timeline */}
          <div className="flex flex-1 flex-col min-w-0">
            <GraphCanvas />
            <RunTimeline />
          </div>

          {/* Right drawer: Node detail */}
          {selectedNodeId && <NodeDrawer />}
        </div>
      </div>
    </div>
  );
}
