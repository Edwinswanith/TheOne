"use client";

import { FormEvent, useEffect, useState } from "react";
import { useAppStore } from "@/lib/store";
import type { CreateProjectPayload } from "@/lib/api";
import { Input, TextArea, Select } from "@/components/ui/form-fields";
import { Plus, TrendingUp, Box, Rocket, Users } from "lucide-react";

const CATEGORIES = [
  { value: "b2b_saas", label: "B2B SaaS" },
  { value: "b2b_services", label: "B2B Services" },
  { value: "b2c", label: "B2C" },
];

const COMPLIANCE = [
  { value: "none", label: "None" },
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
];

const PILLAR_ICONS = [
  { name: "Market to Money", icon: TrendingUp, desc: "ICP, positioning, pricing, channels" },
  { name: "Product", icon: Box, desc: "Strategy, architecture, competitive edge" },
  { name: "Execution", icon: Rocket, desc: "Validation sprints, outbound, assets" },
  { name: "People & Cash", icon: Users, desc: "Team, funding, runway requirements" },
];

export function HomeScreen() {
  const projects = useAppStore((s) => s.projects);
  const loadProjects = useAppStore((s) => s.loadProjects);
  const doCreateProject = useAppStore((s) => s.createProject);
  const openProject = useAppStore((s) => s.openProject);
  const error = useAppStore((s) => s.error);
  const clearError = useAppStore((s) => s.clearError);
  const [creating, setCreating] = useState(false);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    loadProjects();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setCreating(true);
    clearError();
    const fd = new FormData(e.currentTarget);
    const payload: CreateProjectPayload = {
      project_name: fd.get("project_name") as string,
      idea: {
        name: fd.get("idea_name") as string,
        one_liner: fd.get("one_liner") as string,
        problem: fd.get("problem") as string,
        target_region: fd.get("region") as string,
        category: fd.get("category") as string,
      },
      constraints: {
        team_size: Number(fd.get("team_size")) || 1,
        timeline_weeks: Number(fd.get("timeline")) || 8,
        budget_usd_monthly: Number(fd.get("budget")) || 0,
        compliance_level: fd.get("compliance") as string,
      },
    };
    await doCreateProject(payload);
    setCreating(false);
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
              <p className="text-sm text-graphite">Start with your idea and constraints</p>
            </div>
          </button>
        ) : (
          <form
            onSubmit={handleSubmit}
            className="sketch-rounded sketch-border bg-white/90 p-6 shadow-card animate-fade-in"
          >
            <h2 className="text-2xl font-semibold text-ink mb-6">Create Project</h2>

            <div className="grid gap-5 md:grid-cols-2">
              {/* Left: Idea */}
              <div className="space-y-4">
                <h3 className="text-sm font-accent font-semibold tracking-wider text-graphite">Idea</h3>
                <Input name="project_name" label="Project Name" placeholder="My GTM Project" required voiceEnabled />
                <Input name="idea_name" label="Product Name" placeholder="PulsePilot" required voiceEnabled />
                <Input name="one_liner" label="One-Liner" placeholder="AI assistant that turns calls into follow-ups" required voiceEnabled />
                <TextArea name="problem" label="Problem" placeholder="Teams forget follow-ups and lose deals" required voiceEnabled />
                <Input name="region" label="Region" placeholder="US, UK, EU..." required voiceEnabled />
                <Select name="category" label="Category" options={CATEGORIES} />
              </div>

              {/* Right: Constraints */}
              <div className="space-y-4">
                <h3 className="text-sm font-accent font-semibold tracking-wider text-graphite">Constraints</h3>
                <Input name="team_size" label="Team Size" type="number" placeholder="2" defaultValue="2" />
                <Input name="timeline" label="Timeline (weeks)" type="number" placeholder="8" defaultValue="8" />
                <Input name="budget" label="Monthly Budget (USD)" type="number" placeholder="500" defaultValue="500" />
                <Select name="compliance" label="Compliance Level" options={COMPLIANCE} />
              </div>
            </div>

            <div className="mt-6 flex items-center gap-3">
              <button
                type="submit"
                disabled={creating}
                className="sketch-rounded bg-sage px-6 py-2.5 text-sm font-semibold text-white shadow-sm transition-all hover:bg-ink hover:shadow-md disabled:opacity-50"
              >
                {creating ? "Creating..." : "Create & Open Workspace"}
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

      {/* 4-Pillar overview */}
      <div className="mt-12 animate-fade-in" style={{ animationDelay: "0.3s" }}>
        <h2 className="text-xl font-semibold text-ink mb-4 text-center">
          <span className="sketch-underline">4-Pillar Decision Framework</span>
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
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
    </div>
  );
}

