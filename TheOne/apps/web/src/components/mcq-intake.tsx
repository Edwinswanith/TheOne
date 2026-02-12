"use client";

import { useEffect, useMemo, useState } from "react";
import { useAppStore } from "@/lib/store";
import type { ClarificationQuestion, ClarificationOption } from "@/lib/api";
import { CheckCircle, HelpCircle, ChevronRight, Loader2, PenLine, Lightbulb } from "lucide-react";

const CATEGORY_LABELS: Record<string, string> = {
  customer: "Customer",
  market: "Market",
  value: "Value Proposition",
  product: "Product",
  execution: "Execution",
};

const CATEGORY_ORDER = ["customer", "market", "value", "product", "execution"];

export default function McqIntake() {
  const {
    mcqQuestions,
    mcqAnswers,
    mcqLoading,
    loadMcqQuestions,
    setMcqAnswer,
    submitMcq,
  } = useAppStore();

  useEffect(() => {
    if (mcqQuestions.length === 0) {
      loadMcqQuestions();
    }
  }, [mcqQuestions.length, loadMcqQuestions]);

  const answeredCount = Object.keys(mcqAnswers).length;
  const requiredQuestions = mcqQuestions.filter((q: ClarificationQuestion) => q.required);
  const requiredAnswered = requiredQuestions.filter((q: ClarificationQuestion) => mcqAnswers[q.id]).length;
  const allRequiredDone = requiredAnswered === requiredQuestions.length;
  const progressPct = mcqQuestions.length > 0 ? (answeredCount / mcqQuestions.length) * 100 : 0;

  // Group questions by category
  const grouped = useMemo(() => {
    const map: Record<string, ClarificationQuestion[]> = {};
    for (const q of mcqQuestions as ClarificationQuestion[]) {
      const cat = q.category || "other";
      if (!map[cat]) map[cat] = [];
      map[cat].push(q);
    }
    return map;
  }, [mcqQuestions]);

  const orderedCategories = useMemo(() => {
    const cats = Object.keys(grouped);
    return CATEGORY_ORDER.filter((c) => cats.includes(c)).concat(
      cats.filter((c) => !CATEGORY_ORDER.includes(c))
    );
  }, [grouped]);

  if (mcqLoading && mcqQuestions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4 text-[#4b5563]">
        <Loader2 className="w-8 h-8 animate-spin text-[#6d8a73]" />
        <p className="text-sm">Generating clarification questions...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-hidden bg-[#f7f2e8]">
      {/* Header */}
      <div className="shrink-0 border-b border-[#e5dcc9] bg-[#fffaf2] px-6 py-4">
        <h2 className="font-['Source_Serif_4',Georgia,serif] text-xl text-[#1f2328]">
          Clarify Your Strategy
        </h2>
        <p className="text-sm text-[#4b5563] mt-1">
          Confirm or adjust our assumptions before running the analysis.
        </p>
        {/* Progress bar */}
        <div className="mt-3 flex items-center gap-3">
          <div className="flex-1 h-2 bg-[#e5dcc9] rounded-full overflow-hidden">
            <div
              className="h-full bg-[#6d8a73] rounded-full transition-all duration-300"
              style={{ width: `${progressPct}%` }}
            />
          </div>
          <span className="text-xs text-[#4b5563] whitespace-nowrap">
            {answeredCount} of {mcqQuestions.length} answered
          </span>
        </div>
      </div>

      {/* Questions grouped by category */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-6">
        {orderedCategories.map((cat) => {
          const questions = grouped[cat] || [];
          return (
            <div key={cat}>
              <div className="flex items-center gap-2 mb-3">
                <div className="h-px flex-1 bg-[#e5dcc9]" />
                <span className="text-xs font-semibold uppercase tracking-wider text-[#4b5563]">
                  {CATEGORY_LABELS[cat] || cat}
                </span>
                <div className="h-px flex-1 bg-[#e5dcc9]" />
              </div>
              <div className="space-y-4">
                {questions.map((q) => (
                  <QuestionCard
                    key={q.id}
                    question={q}
                    selected={mcqAnswers[q.id]?.optionId ?? null}
                    customValue={mcqAnswers[q.id]?.customValue ?? ""}
                    onSelect={(optId, customVal) => setMcqAnswer(q.id, optId, customVal)}
                    optional={!q.required}
                  />
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="shrink-0 border-t border-[#e5dcc9] bg-[#fffaf2] px-6 py-4">
        <button
          onClick={submitMcq}
          disabled={!allRequiredDone || mcqLoading}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed bg-[#6d8a73] text-white hover:bg-[#5a7a63]"
        >
          {mcqLoading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <>
              Confirm & Start Analysis
              <ChevronRight className="w-4 h-4" />
            </>
          )}
        </button>
        {!allRequiredDone && (
          <p className="text-xs text-[#d58c2f] mt-2 text-center">
            Answer all {requiredQuestions.length} required questions to continue
          </p>
        )}
      </div>
    </div>
  );
}

function QuestionCard({
  question,
  selected,
  customValue,
  onSelect,
  optional = false,
}: {
  question: ClarificationQuestion;
  selected: string | null;
  customValue: string;
  onSelect: (optionId: string, customValue?: string) => void;
  optional?: boolean;
}) {
  const isAnswered = !!selected;
  const [showCustom, setShowCustom] = useState(selected === "custom");
  const [hoveredReasoning, setHoveredReasoning] = useState<string | null>(null);

  return (
    <div
      className={`rounded-lg border p-4 transition-colors ${
        isAnswered
          ? "border-[#6d8a73]/30 bg-[#6d8a73]/5"
          : optional
          ? "border-dashed border-[#e5dcc9] bg-[#fffaf2]"
          : "border-[#e5dcc9] bg-[#fffaf2]"
      }`}
    >
      <div className="flex items-start gap-2 mb-3">
        {isAnswered ? (
          <CheckCircle className="w-5 h-5 text-[#6d8a73] shrink-0 mt-0.5" />
        ) : (
          <HelpCircle className="w-5 h-5 text-[#4b5563] shrink-0 mt-0.5" />
        )}
        <div className="flex-1">
          <h3 className="text-sm font-medium text-[#1f2328]">{question.question}</h3>
          {question.why && (
            <p className="text-xs text-[#4b5563] mt-1">{question.why}</p>
          )}
        </div>
        {question.required && (
          <span className="text-[10px] uppercase tracking-wide text-[#d58c2f] font-medium shrink-0">
            Required
          </span>
        )}
      </div>

      <div className="space-y-2 ml-7">
        {question.options.map((opt: ClarificationOption) => {
          const isSelected = selected === opt.id;
          const isRecommended = opt.recommended;
          const showReasoningHere = hoveredReasoning === opt.id && opt.reasoning;

          return (
            <div key={opt.id}>
              <button
                onClick={() => {
                  onSelect(opt.id);
                  setShowCustom(false);
                }}
                className={`w-full text-left px-3 py-2.5 rounded-md border text-sm transition-all ${
                  isSelected
                    ? "border-[#6d8a73] bg-[#6d8a73]/10 ring-1 ring-[#6d8a73]/20"
                    : isRecommended
                    ? "border-[#6d8a73]/40 bg-[#6d8a73]/5 hover:bg-[#6d8a73]/10"
                    : "border-[#e5dcc9] hover:bg-[#f0ebe0]"
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className="font-medium text-[#1f2328]">{opt.label}</span>
                  {isRecommended && (
                    <span
                      className="text-[10px] uppercase tracking-wide text-[#6d8a73] bg-[#6d8a73]/10 px-1.5 py-0.5 rounded font-medium cursor-help inline-flex items-center gap-1"
                      onMouseEnter={() => setHoveredReasoning(opt.id)}
                      onMouseLeave={() => setHoveredReasoning(null)}
                    >
                      Recommended
                      {opt.reasoning && <Lightbulb size={10} />}
                    </span>
                  )}
                </div>
                {opt.detail && (
                  <p className="text-xs text-[#4b5563] mt-0.5">{opt.detail}</p>
                )}
              </button>
              {showReasoningHere && (
                <div className="mt-1 ml-3 px-3 py-2 rounded-md bg-[#6d8a73]/5 border border-[#6d8a73]/20 text-xs text-[#4b5563] italic flex items-start gap-1.5">
                  <Lightbulb size={12} className="text-[#6d8a73] shrink-0 mt-0.5" />
                  {opt.reasoning}
                </div>
              )}
            </div>
          );
        })}

        {/* Custom text input */}
        {question.allow_custom && (
          <div>
            {!showCustom ? (
              <button
                onClick={() => {
                  setShowCustom(true);
                  onSelect("custom", customValue);
                }}
                className={`w-full text-left px-3 py-2.5 rounded-md border text-sm transition-all flex items-center gap-2 ${
                  selected === "custom"
                    ? "border-[#6d8a73] bg-[#6d8a73]/10 ring-1 ring-[#6d8a73]/20"
                    : "border-dashed border-[#e5dcc9] hover:bg-[#f0ebe0] text-[#4b5563]"
                }`}
              >
                <PenLine size={14} className="shrink-0" />
                <span className="font-medium">Write your own answer</span>
              </button>
            ) : (
              <div
                className={`rounded-md border p-3 transition-all ${
                  selected === "custom"
                    ? "border-[#6d8a73] bg-[#6d8a73]/5 ring-1 ring-[#6d8a73]/20"
                    : "border-[#e5dcc9] bg-[#fffaf2]"
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <PenLine size={14} className="text-[#6d8a73] shrink-0" />
                  <span className="text-sm font-medium text-[#1f2328]">Custom answer</span>
                  <button
                    onClick={() => {
                      setShowCustom(false);
                      if (selected === "custom") onSelect("", "");
                    }}
                    className="ml-auto text-xs text-[#4b5563] hover:text-[#1f2328]"
                  >
                    Cancel
                  </button>
                </div>
                <textarea
                  value={customValue}
                  onChange={(e) => onSelect("custom", e.target.value)}
                  placeholder={question.custom_placeholder || "Enter your own answer..."}
                  rows={2}
                  className="w-full text-sm rounded-md border border-[#e5dcc9] bg-white px-3 py-2 text-[#1f2328] placeholder:text-[#b5b0a3] focus:outline-none focus:border-[#6d8a73] focus:ring-1 focus:ring-[#6d8a73]/30 resize-none"
                />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
