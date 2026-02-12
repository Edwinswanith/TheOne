"use client";

import { useAppStore } from "@/lib/store";
import {
  ArrowRight,
  BarChart3,
  FileSearch,
  GitBranch,
  ShieldCheck,
  Target,
  Users,
  Zap,
} from "lucide-react";

const PILLARS = [
  {
    icon: Target,
    title: "Market to Money",
    color: "#6d8a73",
    description:
      "ICP definition, positioning wedge, pricing model, channel strategy, and sales motion — all evidence-backed.",
  },
  {
    icon: Zap,
    title: "Product",
    color: "#5b7bb4",
    description:
      "Core offer validation, tech feasibility, security & compliance checks, and build-vs-buy analysis.",
  },
  {
    icon: BarChart3,
    title: "Execution",
    color: "#d58c2f",
    description:
      "30-day playbook with daily actions, kill criteria, validation experiments, and asset generation.",
  },
  {
    icon: Users,
    title: "People & Cash",
    color: "#8b5bad",
    description:
      "Team plan, runway math, hiring triggers, and budget allocation aligned to your constraints.",
  },
];

const FEATURES = [
  {
    icon: FileSearch,
    title: "Evidence-Backed",
    description:
      "Every claim is linked to real market data, competitor analysis, or pricing benchmarks.",
  },
  {
    icon: GitBranch,
    title: "Decision Gates",
    description:
      "5 key decisions with AI recommendations. Override any with justification — downstream nodes auto-update.",
  },
  {
    icon: ShieldCheck,
    title: "Contradiction Detection",
    description:
      "14 validation rules catch conflicts between your decisions before they become costly mistakes.",
  },
];

export function LandingPage() {
  const setScreen = useAppStore((s) => s.setScreen);

  return (
    <div className="min-h-screen bg-[#faf8f3]">
      {/* Hero */}
      <header className="relative overflow-hidden">
        <div className="mx-auto max-w-5xl px-6 pt-20 pb-16 text-center">
          <div className="mb-6 inline-flex items-center gap-2 sketch-rounded border border-sage/30 bg-sage/5 px-4 py-1.5 text-sm text-sage font-medium">
            <Zap size={14} />
            Evidence-backed GTM planning
          </div>

          <h1 className="font-accent text-5xl font-bold leading-tight text-ink md:text-6xl">
            From idea to
            <span className="relative mx-2 text-sage">
              execution plan
              <svg
                className="absolute -bottom-2 left-0 w-full"
                viewBox="0 0 300 12"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M2 8C60 3 140 2 298 6"
                  stroke="#6d8a73"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  opacity="0.4"
                />
              </svg>
            </span>
            <br />
            in one session.
          </h1>

          <p className="mx-auto mt-6 max-w-2xl text-lg text-graphite leading-relaxed">
            GTMGraph turns your product idea into a decision-complete, evidence-linked
            go-to-market plan across 4 pillars — with accountable overrides and a
            30-day playbook.
          </p>

          <button
            onClick={() => setScreen("home")}
            className="mt-10 inline-flex items-center gap-2 sketch-rounded bg-sage px-8 py-3.5 text-base font-semibold text-white shadow-sm transition-all hover:bg-sage/90 hover:shadow-md active:scale-[0.98]"
          >
            Get Started
            <ArrowRight size={18} />
          </button>
        </div>
      </header>

      {/* 4 Pillars */}
      <section className="mx-auto max-w-5xl px-6 py-16">
        <h2 className="text-center font-accent text-3xl font-bold text-ink mb-3">
          4 Pillars, One Graph
        </h2>
        <p className="text-center text-graphite mb-12 max-w-lg mx-auto">
          Every go-to-market plan needs answers across four dimensions.
          GTMGraph covers all of them.
        </p>

        <div className="grid gap-5 sm:grid-cols-2">
          {PILLARS.map((pillar) => (
            <div
              key={pillar.title}
              className="sketch-rounded border border-stone-200 bg-white p-6 transition-shadow hover:shadow-md"
            >
              <div className="flex items-center gap-3 mb-3">
                <span
                  className="flex h-10 w-10 items-center justify-center sketch-rounded text-white"
                  style={{ background: pillar.color }}
                >
                  <pillar.icon size={20} strokeWidth={1.5} />
                </span>
                <h3 className="text-lg font-semibold text-ink">{pillar.title}</h3>
              </div>
              <p className="text-sm text-graphite leading-relaxed">
                {pillar.description}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="bg-white/60 border-y border-stone-200">
        <div className="mx-auto max-w-5xl px-6 py-16">
          <h2 className="text-center font-accent text-3xl font-bold text-ink mb-12">
            Built for rigor
          </h2>

          <div className="grid gap-8 sm:grid-cols-3">
            {FEATURES.map((feature) => (
              <div key={feature.title} className="text-center">
                <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center sketch-rounded bg-sage/10">
                  <feature.icon size={24} strokeWidth={1.5} className="text-sage" />
                </div>
                <h3 className="text-base font-semibold text-ink mb-2">
                  {feature.title}
                </h3>
                <p className="text-sm text-graphite leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-5xl px-6 py-20 text-center">
        <h2 className="font-accent text-3xl font-bold text-ink mb-4">
          Ready to plan your GTM?
        </h2>
        <p className="text-graphite mb-8 max-w-md mx-auto">
          Describe your idea, answer 5 questions, and get an evidence-backed
          execution plan in minutes.
        </p>
        <button
          onClick={() => setScreen("home")}
          className="inline-flex items-center gap-2 sketch-rounded bg-sage px-8 py-3.5 text-base font-semibold text-white shadow-sm transition-all hover:bg-sage/90 hover:shadow-md active:scale-[0.98]"
        >
          Start Planning
          <ArrowRight size={18} />
        </button>
      </section>

      {/* Footer */}
      <footer className="border-t border-stone-200 py-8 text-center text-xs text-graphite">
        GTMGraph &mdash; Evidence-backed go-to-market planning
      </footer>
    </div>
  );
}
