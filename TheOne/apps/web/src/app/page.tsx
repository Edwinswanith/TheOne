"use client";

import { useAppStore } from "@/lib/store";
import { HomeScreen } from "@/components/home-screen";
import { ChatIntakeScreen } from "@/components/chat-intake";
import { DecisionGateScreen } from "@/components/decision-gate";
import { WorkspaceShell } from "@/components/workspace-shell";
import McqIntake from "@/components/mcq-intake";

export default function HomePage() {
  const screen = useAppStore((s) => s.screen);

  if (screen === "chat") {
    return <ChatIntakeScreen />;
  }
  if (screen === "mcq") {
    return <McqIntake />;
  }
  if (screen === "decisions") {
    return <DecisionGateScreen />;
  }
  if (screen === "workspace") {
    return <WorkspaceShell />;
  }

  return <HomeScreen />;
}
