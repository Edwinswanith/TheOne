"use client";

import { useState } from "react";
import { useAppStore } from "@/lib/store";
import * as api from "@/lib/api";
import { Zap, Send, Globe, Users, Check } from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface Track {
  id: string;
  title: string;
  description: string;
  icon: LucideIcon;
  duration: string;
}

const TRACKS: Track[] = [
  {
    id: "validation_sprint",
    title: "Validation Sprint",
    description: "Rapid customer discovery — 10 interviews, test core hypothesis, validate willingness to pay.",
    icon: Zap,
    duration: "2 weeks",
  },
  {
    id: "outbound_sprint",
    title: "Outbound Sprint",
    description: "50 targeted outreach messages, book 5+ demos, measure response rate and objections.",
    icon: Send,
    duration: "3 weeks",
  },
  {
    id: "landing_waitlist",
    title: "Landing + Waitlist",
    description: "Ship a landing page with CTA, drive traffic via content, measure signup conversion.",
    icon: Globe,
    duration: "2 weeks",
  },
  {
    id: "pilot_onboarding",
    title: "Pilot Onboarding",
    description: "Onboard 2-3 design partners, ship MVP, collect usage data and NPS.",
    icon: Users,
    duration: "4 weeks",
  },
];

export function ExecutionTrackPicker({ onComplete }: { onComplete?: () => void }) {
  const activeScenarioId = useAppStore((s) => s.activeScenarioId);
  const refreshScenario = useAppStore((s) => s.refreshScenario);
  const scenarioState = useAppStore((s) => s.scenarioState);
  const [selected, setSelected] = useState<string>(
    scenarioState?.execution?.chosen_track || "unset"
  );
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    if (!activeScenarioId || selected === "unset") return;
    setSaving(true);
    try {
      await api.setExecutionTrack(activeScenarioId, selected);
      await refreshScenario();
      onComplete?.();
    } catch (e) {
      useAppStore.setState({ error: (e as Error).message });
    }
    setSaving(false);
  }

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold text-ink font-accent">Choose Execution Track</h3>
        <p className="text-sm text-graphite mt-1">
          Select how you want to validate your GTM plan in the first 30 days.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {TRACKS.map((track) => {
          const Icon = track.icon;
          const isSelected = selected === track.id;
          return (
            <button
              key={track.id}
              onClick={() => setSelected(track.id)}
              className={`text-left sketch-rounded border p-4 transition-all ${
                isSelected
                  ? "border-sage ring-2 ring-sage/30 bg-sage/5"
                  : "border-stone-200 hover:border-stone-300 bg-white"
              }`}
            >
              <div className="flex items-start gap-3">
                <div
                  className={`flex h-8 w-8 items-center justify-center sketch-rounded ${
                    isSelected ? "bg-sage text-white" : "bg-stone-100 text-graphite"
                  }`}
                >
                  <Icon size={16} strokeWidth={1.5} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-ink">{track.title}</span>
                    <span className="text-[10px] text-graphite bg-stone-100 sketch-rounded px-1.5 py-0.5">
                      {track.duration}
                    </span>
                  </div>
                  <p className="text-xs text-graphite mt-1 leading-relaxed">{track.description}</p>
                </div>
                {isSelected && <Check size={16} className="text-sage mt-1" />}
              </div>
            </button>
          );
        })}
      </div>

      <div className="flex justify-end pt-2">
        <button
          onClick={handleSave}
          disabled={saving || selected === "unset"}
          className="sketch-rounded bg-sage px-5 py-2 text-sm font-semibold text-white hover:bg-ink disabled:opacity-50 transition-all"
        >
          {saving ? "Saving..." : "Set Execution Track"}
        </button>
      </div>
    </div>
  );
}
