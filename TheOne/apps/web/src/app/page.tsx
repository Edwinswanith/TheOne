"use client";

import { useAppStore } from "@/lib/store";
import { HomeScreen } from "@/components/home-screen";
import { IntakeScreen } from "@/components/intake-screen";
import { WorkspaceShell } from "@/components/workspace-shell";

export default function HomePage() {
  const screen = useAppStore((s) => s.screen);

  if (screen === "intake") {
    return <IntakeScreen />;
  }
  if (screen === "workspace") {
    return <WorkspaceShell />;
  }

  return <HomeScreen />;
}
