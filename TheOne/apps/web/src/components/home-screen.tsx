"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { useAppStore } from "@/lib/store";
import { CreationProgress } from "@/components/creation-progress";
import { useSpeechInput } from "@/hooks/use-speech-input";
import { Plus, TrendingUp, Box, Rocket, Users, Mic, Square, Loader2, AudioLines, Tag, Zap } from "lucide-react";

const PILLAR_ICONS = [
  { name: "Market Intelligence", icon: TrendingUp, desc: "Evidence gathering, competitive teardown" },
  { name: "Customer", icon: Users, desc: "ICP definition, buyer personas, segments" },
  { name: "Positioning & Pricing", icon: Tag, desc: "Value proposition, pricing models" },
  { name: "Go-to-Market", icon: Rocket, desc: "Channels, sales motions, outbound" },
  { name: "Product & Tech", icon: Box, desc: "Strategy, architecture, feasibility" },
  { name: "Execution", icon: Zap, desc: "Sprints, milestones, team, funding" },
];

export function HomeScreen() {
  const projects = useAppStore((s) => s.projects);
  const loadProjects = useAppStore((s) => s.loadProjects);
  const createFromContext = useAppStore((s) => s.createFromContext);
  const creatingFromContext = useAppStore((s) => s.creatingFromContext);
  const openProject = useAppStore((s) => s.openProject);
  const error = useAppStore((s) => s.error);
  const clearError = useAppStore((s) => s.clearError);
  const [showForm, setShowForm] = useState(false);
  const [context, setContext] = useState("");
  const [projectName, setProjectName] = useState("");

  const onTranscript = useCallback((text: string) => {
    setContext((prev) => (prev ? `${prev} ${text}` : text));
  }, []);
  const { state: speechState, interim, elapsed, toggle: toggleSpeech, supported: speechSupported } = useSpeechInput(onTranscript);

  useEffect(() => {
    loadProjects();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (creatingFromContext) {
    return <CreationProgress />;
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (context.trim().length < 10) return;
    clearError();
    await createFromContext(context.trim(), projectName.trim() || undefined);
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-12 md:px-8">
      {/* Header */}
      <div className="mb-10 text-center animate-fade-in">
        <h1 className="text-5xl font-bold text-ink tracking-tight">
          <span className="font-accent text-6xl">GTMGraph</span>
        </h1>
        <p className="mt-3 text-lg text-graphite max-w-xl mx-auto">
          Evidence-backed go-to-market planning. Turn your idea into a
          decision-complete execution graph in under 30 minutes.
        </p>
      </div>

      {error && (
        <div className="mb-6 sketch-rounded sketch-border bg-red-50 px-4 py-3 text-sm text-red-700 animate-fade-in">
          {error}
          <button onClick={clearError} className="ml-3 font-medium underline">Dismiss</button>
        </div>
      )}

      {/* New Project */}
      <div className="mb-8 animate-fade-in" style={{ animationDelay: "0.1s" }}>
        {!showForm ? (
          <button
            onClick={() => setShowForm(true)}
            className="group flex w-full items-center gap-4 sketch-rounded border-2 border-dashed border-stone-300 bg-white/60 p-6 text-left transition-all hover:border-sage hover:bg-white/80 hover:shadow-card hover:animate-wiggle"
          >
            <div className="flex h-12 w-12 shrink-0 items-center justify-center sketch-rounded bg-sage/10 text-sage transition-colors group-hover:bg-sage group-hover:text-white">
              <Plus size={24} strokeWidth={1.5} />
            </div>
            <div>
              <p className="text-lg font-semibold text-ink">New Project</p>
              <p className="text-sm text-graphite">Describe your idea and we&apos;ll build your GTM plan</p>
            </div>
          </button>
        ) : (
          <form
            onSubmit={handleSubmit}
            className="sketch-rounded sketch-border bg-white/90 p-6 shadow-card animate-fade-in"
          >
            <h2 className="text-2xl font-semibold text-ink mb-6">Create Project</h2>

            <div className="space-y-4">
              <div>
                <label htmlFor="project_name" className="block text-xs font-medium text-graphite mb-1">
                  Project name (optional)
                </label>
                <input
                  id="project_name"
                  type="text"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  placeholder="My GTM Project"
                  className="w-full sketch-rounded border border-stone-300 bg-white px-3 py-2 text-sm text-ink placeholder:text-stone-400 focus:border-sage focus:outline-none focus:ring-2 focus:ring-sage/20"
                />
              </div>

              <div>
                <label htmlFor="context" className="block text-xs font-medium text-graphite mb-1">
                  Describe your idea
                </label>
                <textarea
                  id="context"
                  value={context}
                  onChange={(e) => setContext(e.target.value)}
                  rows={6}
                  placeholder={"Tell us about your product idea, the problem it solves, who it's for, and any context about your market.\n\nFor example: \"We're building an AI-powered call assistant for B2B sales teams. It listens to sales calls, auto-generates follow-up emails, and updates the CRM. We're targeting mid-market SaaS companies (50-500 employees) in the US. The main problem is that reps forget follow-ups and lose deals. We have a team of 3, $2k/month budget, and want to launch in 8 weeks.\""}
                  className="w-full sketch-rounded border border-stone-300 bg-white px-3 py-3 text-sm text-ink placeholder:text-stone-400 focus:border-sage focus:outline-none focus:ring-2 focus:ring-sage/20 resize-none leading-relaxed"
                />

                {/* Voice input area */}
                {speechState === "idle" && speechSupported && (
                  <div className="mt-3 flex items-center gap-3">
                    <button
                      type="button"
                      onClick={toggleSpeech}
                      className="flex items-center gap-2 sketch-rounded border border-stone-300 bg-white px-3.5 py-2 text-xs font-medium text-graphite transition-all hover:border-sage hover:text-sage hover:bg-sage/5"
                    >
                      <Mic size={14} strokeWidth={1.5} />
                      Speak your idea
                    </button>
                    <span className="text-[11px] text-stone-400">or type above</span>
                  </div>
                )}

                {/* Recording overlay */}
                {speechState === "listening" && (
                  <div className="mt-3 sketch-rounded border-2 border-red-200 bg-red-50/50 px-4 py-3 animate-fade-in">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="relative flex h-3 w-3">
                          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400 opacity-75" />
                          <span className="relative inline-flex h-3 w-3 rounded-full bg-red-500" />
                        </span>
                        <span className="text-sm font-medium text-red-700">Listening...</span>
                        <span className="font-mono text-xs text-red-400">{elapsed}</span>
                      </div>
                      <button
                        type="button"
                        onClick={toggleSpeech}
                        className="flex items-center gap-1.5 sketch-rounded bg-red-500 px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-red-600"
                      >
                        <Square size={10} strokeWidth={2} fill="currentColor" />
                        Stop
                      </button>
                    </div>

                    {/* Waveform bars */}
                    <div className="mt-3 flex items-end justify-center gap-[3px] h-8">
                      {Array.from({ length: 24 }).map((_, i) => (
                        <div
                          key={i}
                          className="w-1 rounded-full bg-red-300"
                          style={{
                            animation: `waveform 0.8s ease-in-out ${i * 0.05}s infinite alternate`,
                          }}
                        />
                      ))}
                    </div>

                    {/* Live interim transcript */}
                    {interim && (
                      <p className="mt-2 text-xs text-red-600/70 italic truncate">
                        {interim}
                      </p>
                    )}
                  </div>
                )}

                {/* Processing state */}
                {speechState === "processing" && (
                  <div className="mt-3 sketch-rounded border border-sage/30 bg-sage/5 px-4 py-3 animate-fade-in">
                    <div className="flex items-center gap-2">
                      <Loader2 size={14} strokeWidth={1.5} className="animate-spin text-sage" />
                      <span className="text-sm font-medium text-sage">Adding to your description...</span>
                    </div>
                  </div>
                )}

                {/* Error state */}
                {speechState === "error" && (
                  <div className="mt-3 sketch-rounded border border-amber-200 bg-amber-50 px-4 py-3 animate-fade-in">
                    <div className="flex items-center gap-2">
                      <AudioLines size={14} strokeWidth={1.5} className="text-amber-500" />
                      <span className="text-sm text-amber-700">
                        Voice input unavailable. Please check microphone permissions.
                      </span>
                    </div>
                  </div>
                )}

                <p className="mt-2 text-[11px] text-stone-400">
                  Include as much context as you can — product, market, team size, budget, timeline. We&apos;ll extract the details and ask follow-up questions.
                </p>
              </div>
            </div>

            <div className="mt-6 flex items-center gap-3">
              <button
                type="submit"
                disabled={context.trim().length < 10}
                className="sketch-rounded bg-sage px-6 py-2.5 text-sm font-semibold text-white shadow-sm transition-all hover:bg-ink hover:shadow-md disabled:opacity-50"
              >
                Create Project
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="sketch-rounded px-4 py-2.5 text-sm font-medium text-graphite hover:text-ink transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        )}
      </div>

      {/* Existing Projects */}
      {projects.length > 0 && (
        <div className="animate-fade-in" style={{ animationDelay: "0.2s" }}>
          <h2 className="text-xl font-semibold text-ink mb-4">Your Projects</h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {projects.map((p) => (
              <button
                key={p.id}
                onClick={() => {
                  openProject(p.id, p.scenario_ids?.[0] ?? "");
                }}
                className="group sketch-card bg-white/80 p-5 text-left hover:border-sage"
              >
                <p className="font-semibold text-ink group-hover:text-sage transition-colors">{p.name}</p>
                <p className="mt-1 text-xs text-graphite">
                  {new Date(p.created_at).toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                  })}
                </p>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 6-Pillar overview */}
      <div className="mt-12 animate-fade-in" style={{ animationDelay: "0.3s" }}>
        <h2 className="text-xl font-semibold text-ink mb-4 text-center">
          <span className="sketch-underline">6-Pillar Decision Framework</span>
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {PILLAR_ICONS.map((pillar) => {
            const Icon = pillar.icon;
            return (
              <div
                key={pillar.name}
                className="sketch-card bg-white/70 p-4 text-center"
              >
                <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center sketch-rounded bg-sage/10 text-sage">
                  <Icon size={20} strokeWidth={1.5} />
                </div>
                <h3 className="text-sm font-semibold text-ink">{pillar.name}</h3>
                <p className="mt-1 text-xs text-graphite font-accent">{pillar.desc}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Waveform keyframes */}
      <style jsx global>{`
        @keyframes waveform {
          0% { height: 4px; }
          100% { height: 28px; }
        }
      `}</style>
    </div>
  );
}
