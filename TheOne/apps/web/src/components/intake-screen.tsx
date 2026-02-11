"use client";

import { FormEvent, useState } from "react";
import { useAppStore } from "@/lib/store";
import { TextArea } from "@/components/ui/form-fields";
import { ArrowLeft, ArrowRight } from "lucide-react";

const INTAKE_FIELDS = [
  {
    id: "buyer_role",
    label: "Who is the buyer?",
    placeholder: "e.g. VP of Sales at mid-market SaaS companies",
  },
  {
    id: "company_type",
    label: "What type of company?",
    placeholder: "e.g. B2B SaaS with 50-500 employees, $5M-$50M ARR",
  },
  {
    id: "trigger_event",
    label: "What triggers the purchase?",
    placeholder: "e.g. They just missed quota two quarters in a row",
  },
  {
    id: "current_workaround",
    label: "How do they solve it today?",
    placeholder: "e.g. Manual CRM notes and spreadsheets, occasional coaching sessions",
  },
  {
    id: "measurable_outcome",
    label: "What's the measurable outcome?",
    placeholder: "e.g. 20% increase in quota attainment within 6 months",
  },
] as const;

export function IntakeScreen() {
  const scenarioState = useAppStore((s) => s.scenarioState);
  const submitIntake = useAppStore((s) => s.submitIntake);
  const setScreen = useAppStore((s) => s.setScreen);
  const error = useAppStore((s) => s.error);
  const clearError = useAppStore((s) => s.clearError);
  const [submitting, setSubmitting] = useState(false);

  const ideaName = scenarioState?.idea?.name ?? "Your Project";
  const oneLiner = scenarioState?.idea?.one_liner ?? "";

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitting(true);
    clearError();

    const fd = new FormData(e.currentTarget);
    const answers = INTAKE_FIELDS.map((field) => ({
      question_id: field.id,
      answer_type: "text" as const,
      value: (fd.get(field.id) as string).trim(),
    }));

    await submitIntake(answers);
    setSubmitting(false);
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-12 md:px-8">
      {/* Back button */}
      <button
        onClick={() => setScreen("home")}
        className="mb-6 flex items-center gap-1.5 text-sm text-graphite hover:text-ink transition-colors"
      >
        <ArrowLeft size={14} strokeWidth={1.5} />
        Back to projects
      </button>

      {/* Header */}
      <div className="mb-8 animate-fade-in">
        <h1 className="text-3xl font-bold text-ink tracking-tight">
          <span className="font-accent">{ideaName}</span>
        </h1>
        {oneLiner && (
          <p className="mt-2 text-graphite">{oneLiner}</p>
        )}
        <p className="mt-4 text-sm text-graphite">
          Answer these 5 questions so the pipeline can build your GTM plan.
          Be as specific as possible for better results.
        </p>
      </div>

      {error && (
        <div className="mb-6 sketch-rounded sketch-border bg-red-50 px-4 py-3 text-sm text-red-700 animate-fade-in">
          {error}
          <button onClick={clearError} className="ml-3 font-medium underline">Dismiss</button>
        </div>
      )}

      {/* Form */}
      <form
        onSubmit={handleSubmit}
        className="sketch-rounded sketch-border bg-white/90 p-6 shadow-card animate-fade-in space-y-5"
      >
        {INTAKE_FIELDS.map((field) => (
          <TextArea
            key={field.id}
            name={field.id}
            label={field.label}
            placeholder={field.placeholder}
            required
            rows={3}
            voiceEnabled
          />
        ))}

        <div className="flex items-center gap-3 pt-2">
          <button
            type="submit"
            disabled={submitting}
            className="flex items-center gap-1.5 sketch-rounded bg-sage px-6 py-2.5 text-sm font-semibold text-white shadow-sm transition-all hover:bg-ink hover:shadow-md disabled:opacity-50"
          >
            {submitting ? "Submitting..." : "Continue to Workspace"}
            {!submitting && <ArrowRight size={14} strokeWidth={1.5} />}
          </button>
        </div>
      </form>
    </div>
  );
}
