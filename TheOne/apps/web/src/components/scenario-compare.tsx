"use client";

import { useEffect, useState } from "react";
import * as api from "@/lib/api";
import type { CompareResult } from "@/lib/api";
import { ArrowLeftRight, TrendingUp, TrendingDown, Minus, AlertTriangle } from "lucide-react";

export function ScenarioCompare({
  leftId,
  rightId,
}: {
  leftId: string;
  rightId: string;
}) {
  const [result, setResult] = useState<CompareResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function compare() {
      setLoading(true);
      try {
        const res = await api.compareScenarios(leftId, rightId);
        setResult(res);
      } catch (e) {
        setError((e as Error).message);
      }
      setLoading(false);
    }
    compare();
  }, [leftId, rightId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-sm text-graphite">Comparing scenarios...</p>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="sketch-rounded sketch-border bg-red-50 px-4 py-3 text-sm text-red-700">
        {error || "Failed to compare scenarios"}
      </div>
    );
  }

  const diffKeys = Object.keys(result.decision_diff);
  const confDelta = result.confidence_delta;
  const riskDelta = result.risk_delta;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <ArrowLeftRight size={18} strokeWidth={1.5} className="text-sage" />
        <h3 className="text-lg font-semibold text-ink font-accent">Scenario Comparison</h3>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-3">
        <div className="sketch-rounded border border-stone-200 bg-white p-4">
          <span className="text-xs text-graphite uppercase tracking-wide">Confidence Delta</span>
          <div className="flex items-center gap-2 mt-1">
            {confDelta > 0 ? (
              <TrendingUp size={16} className="text-sage" />
            ) : confDelta < 0 ? (
              <TrendingDown size={16} className="text-red-500" />
            ) : (
              <Minus size={16} className="text-graphite" />
            )}
            <span className={`text-lg font-bold ${confDelta > 0 ? "text-sage" : confDelta < 0 ? "text-red-500" : "text-graphite"}`}>
              {confDelta > 0 ? "+" : ""}{(confDelta * 100).toFixed(1)}%
            </span>
          </div>
        </div>

        <div className="sketch-rounded border border-stone-200 bg-white p-4">
          <span className="text-xs text-graphite uppercase tracking-wide">Risk Delta</span>
          <div className="flex items-center gap-2 mt-1">
            {riskDelta > 0 ? (
              <AlertTriangle size={16} className="text-amber" />
            ) : riskDelta < 0 ? (
              <TrendingDown size={16} className="text-sage" />
            ) : (
              <Minus size={16} className="text-graphite" />
            )}
            <span className={`text-lg font-bold ${riskDelta > 0 ? "text-amber" : riskDelta < 0 ? "text-sage" : "text-graphite"}`}>
              {riskDelta > 0 ? "+" : ""}{riskDelta} risk{Math.abs(riskDelta) !== 1 ? "s" : ""}
            </span>
          </div>
        </div>
      </div>

      {/* Decision diffs */}
      {diffKeys.length > 0 ? (
        <div className="sketch-rounded border border-stone-200 bg-white">
          <div className="px-4 py-3 border-b border-stone-100">
            <span className="text-sm font-semibold text-ink">
              {diffKeys.length} Decision{diffKeys.length > 1 ? "s" : ""} Differ
            </span>
          </div>
          <div className="divide-y divide-stone-100">
            {diffKeys.map((key) => {
              const diff = result.decision_diff[key];
              return (
                <div key={key} className="px-4 py-3 flex items-center justify-between">
                  <span className="text-sm font-medium text-ink capitalize">
                    {key.replace(/_/g, " ")}
                  </span>
                  <div className="flex items-center gap-3 text-xs">
                    <span className="sketch-rounded bg-stone-100 px-2 py-1 text-graphite">
                      {diff.left || "unset"}
                    </span>
                    <ArrowLeftRight size={12} className="text-graphite" />
                    <span className="sketch-rounded bg-sage/10 px-2 py-1 text-sage font-medium">
                      {diff.right || "unset"}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="text-center py-6 text-sm text-graphite">
          No decision differences between these scenarios.
        </div>
      )}
    </div>
  );
}
