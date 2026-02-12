"use client";

import { useState } from "react";
import { useAppStore } from "@/lib/store";
import * as api from "@/lib/api";
import {
  CheckCircle,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  ArrowRight,
  Shield,
} from "lucide-react";

interface DecisionOption {
  id: string;
  label: string;
  description?: string;
  confidence?: number;
}

interface Decision {
  key: string;
  selected_option_id: string;
  recommended_option_id: string;
  options: DecisionOption[];
  override: { is_custom: boolean; justification: string };
}

export function DecisionGateScreen() {
  const scenarioState = useAppStore((s) => s.scenarioState);
  const activeScenarioId = useAppStore((s) => s.activeScenarioId);
  const setScreen = useAppStore((s) => s.setScreen);
  const refreshScenario = useAppStore((s) => s.refreshScenario);
  const startRun = useAppStore((s) => s.startRun);
  const error = useAppStore((s) => s.error);
  const clearError = useAppStore((s) => s.clearError);

  const [expanded, setExpanded] = useState<string | null>(null);
  const [overrideText, setOverrideText] = useState<Record<string, string>>({});
  const [confirming, setConfirming] = useState(false);
  const [rerunDialog, setRerunDialog] = useState<string | null>(null);

  if (!scenarioState || !activeScenarioId) return null;

  const decisions = scenarioState.decisions;
  const decisionKeys = ["icp", "positioning", "pricing", "channels", "sales_motion"];

  const pendingCount = decisionKeys.filter((key) => {
    const d = decisions[key];
    return !d.selected_option_id || d.selected_option_id === "";
  }).length;

  const allDecided = pendingCount === 0;

  async function acceptRecommended(key: string) {
    const d = decisions[key];
    if (!d.recommended_option_id) return;
    try {
      await api.selectDecision(activeScenarioId!, key, {
        selected_option_id: d.recommended_option_id,
        is_custom: false,
      });
      await refreshScenario();
    } catch (e) {
      useAppStore.setState({ error: (e as Error).message });
    }
  }

  async function overrideDecision(key: string, optionId: string) {
    const justification = overrideText[key] || "";
    if (justification.length < 20) return;
    try {
      await api.selectDecision(activeScenarioId!, key, {
        selected_option_id: optionId,
        is_custom: true,
        justification,
      });
      await refreshScenario();
      setExpanded(null);
    } catch (e) {
      useAppStore.setState({ error: (e as Error).message });
    }
  }

  async function confirmAllDecisions() {
    setConfirming(true);
    setScreen("workspace");
    setConfirming(false);
  }

  async function triggerRerun(key: string) {
    setRerunDialog(null);
    try {
      await api.startRun(activeScenarioId!, key);
      await refreshScenario();
    } catch (e) {
      useAppStore.setState({ error: (e as Error).message });
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-12 md:px-8 animate-fade-in">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Shield size={24} strokeWidth={1.5} className="text-sage" />
          <h1 className="text-2xl font-bold text-ink font-accent">
            {pendingCount > 0
              ? `${pendingCount} Decision${pendingCount > 1 ? "s" : ""} Need${pendingCount === 1 ? "s" : ""} Your Input`
              : "All Decisions Confirmed"}
          </h1>
        </div>
        <p className="text-sm text-graphite">
          Review each decision below. Accept the AI recommendation or override with your own choice.
        </p>
      </div>

      {error && (
        <div className="mb-6 sketch-rounded sketch-border bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
          <button onClick={clearError} className="ml-3 font-medium underline">Dismiss</button>
        </div>
      )}

      {/* Rerun confirmation dialog */}
      {rerunDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
          <div className="sketch-rounded bg-white p-6 shadow-lg max-w-md mx-4">
            <h3 className="text-lg font-semibold text-ink mb-2">Re-evaluate downstream?</h3>
            <p className="text-sm text-graphite mb-4">
              Changing <span className="font-medium">{rerunDialog}</span> will re-evaluate dependent decisions.
              This may take a moment.
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setRerunDialog(null)}
                className="sketch-rounded border border-stone-300 px-4 py-2 text-sm text-graphite hover:bg-stone-50"
              >
                Cancel
              </button>
              <button
                onClick={() => triggerRerun(rerunDialog)}
                className="sketch-rounded bg-sage px-4 py-2 text-sm font-semibold text-white hover:bg-ink"
              >
                Continue
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Decision cards */}
      <div className="space-y-4">
        {decisionKeys.map((key) => {
          const d = decisions[key] as Decision & Record<string, unknown>;
          const options = (d.options || []) as DecisionOption[];
          const recommended = options.find((o) => o.id === d.recommended_option_id);
          const selected = d.selected_option_id;
          const isExpanded = expanded === key;
          const isDecided = selected && selected !== "";

          return (
            <div
              key={key}
              className={`sketch-rounded border bg-white shadow-sm transition-all ${
                isDecided ? "border-sage/30" : "border-amber/40"
              }`}
            >
              {/* Header */}
              <button
                onClick={() => setExpanded(isExpanded ? null : key)}
                className="flex w-full items-center justify-between px-5 py-4 text-left"
              >
                <div className="flex items-center gap-3">
                  {isDecided ? (
                    <CheckCircle size={18} strokeWidth={1.5} className="text-sage" />
                  ) : (
                    <AlertTriangle size={18} strokeWidth={1.5} className="text-amber" />
                  )}
                  <div>
                    <span className="text-sm font-semibold text-ink capitalize">
                      {key.replace(/_/g, " ")}
                    </span>
                    {isDecided && recommended && (
                      <span className="ml-2 text-xs text-graphite">
                        {selected === d.recommended_option_id ? "Recommended" : "Override"}
                      </span>
                    )}
                  </div>
                </div>
                {isExpanded ? (
                  <ChevronUp size={16} className="text-graphite" />
                ) : (
                  <ChevronDown size={16} className="text-graphite" />
                )}
              </button>

              {/* Expanded content */}
              {isExpanded && (
                <div className="border-t border-stone-100 px-5 py-4 space-y-3 animate-fade-in">
                  {/* Recommended option */}
                  {recommended && (
                    <div className="sketch-rounded border border-sage/30 bg-sage/5 p-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="text-xs font-semibold text-sage uppercase tracking-wide">
                            Recommended
                          </span>
                          <p className="text-sm font-medium text-ink mt-1">{recommended.label}</p>
                          {recommended.description && (
                            <p className="text-xs text-graphite mt-0.5">{recommended.description}</p>
                          )}
                        </div>
                        <button
                          onClick={() => acceptRecommended(key)}
                          className="sketch-rounded bg-sage px-3 py-1.5 text-xs font-semibold text-white hover:bg-ink"
                        >
                          Accept
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Alternative options */}
                  {options
                    .filter((o) => o.id !== d.recommended_option_id)
                    .map((opt) => (
                      <div
                        key={opt.id}
                        className="sketch-rounded border border-stone-200 p-3 hover:border-stone-300 transition-colors"
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm font-medium text-ink">{opt.label}</p>
                            {opt.description && (
                              <p className="text-xs text-graphite mt-0.5">{opt.description}</p>
                            )}
                          </div>
                          <button
                            onClick={() => setRerunDialog(key)}
                            className="sketch-rounded border border-stone-300 px-3 py-1.5 text-xs text-graphite hover:text-ink"
                          >
                            Override
                          </button>
                        </div>
                      </div>
                    ))}

                  {/* Override justification */}
                  <div className="pt-2">
                    <label className="block text-xs font-medium text-graphite mb-1">
                      Override justification (min 20 chars)
                    </label>
                    <textarea
                      value={overrideText[key] || ""}
                      onChange={(e) =>
                        setOverrideText((prev) => ({ ...prev, [key]: e.target.value }))
                      }
                      placeholder="Explain why you're overriding..."
                      rows={2}
                      className="w-full sketch-rounded border border-stone-300 bg-white px-3 py-2 text-sm text-ink placeholder:text-stone-400 focus:border-sage focus:outline-none focus:ring-2 focus:ring-sage/20 resize-none"
                    />
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Confirm all button */}
      <div className="mt-8 flex justify-end">
        <button
          onClick={confirmAllDecisions}
          disabled={confirming}
          className="flex items-center gap-2 sketch-rounded bg-sage px-6 py-2.5 text-sm font-semibold text-white shadow-sm transition-all hover:bg-ink hover:shadow-md disabled:opacity-50"
        >
          {confirming ? "Confirming..." : allDecided ? "Continue to Workspace" : "Continue with Current Decisions"}
          <ArrowRight size={14} strokeWidth={1.5} />
        </button>
      </div>
    </div>
  );
}
