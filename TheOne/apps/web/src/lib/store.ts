"use client";

import { create } from "zustand";
import type { RunEvent } from "@/lib/types";
import type {
  CanonicalState,
  ChatResponse,
  CreateProjectPayload,
  GraphNode,
  GraphGroup,
  IntakeAnswer,
  ProjectSummary,
} from "@/lib/api";
import * as api from "@/lib/api";
import { subscribeToRun } from "@/lib/sse";

type Screen = "home" | "chat" | "workspace" | "decisions";

interface ChatMessage {
  role: "assistant" | "user";
  content: string;
  field?: string;
  suggestions?: string[];
}

const REQUIRED_INTAKE = [
  "buyer_role",
  "company_type",
  "trigger_event",
  "current_workaround",
  "measurable_outcome",
];

function needsIntake(state: CanonicalState): boolean {
  const answers = state.inputs?.intake_answers ?? [];
  return REQUIRED_INTAKE.some(
    (id) => !answers.find((a) => a.question_id === id && a.value.trim() !== "")
  );
}

interface AgentStatus {
  name: string;
  status: "pending" | "running" | "completed" | "skipped" | "failed";
  patchCount?: number;
}

interface AppState {
  /* navigation */
  screen: Screen;
  setScreen: (s: Screen) => void;

  /* projects */
  projects: ProjectSummary[];
  loadProjects: () => Promise<void>;
  createProject: (p: CreateProjectPayload) => Promise<void>;
  createFromContext: (context: string, projectName?: string) => Promise<void>;

  /* creation progress */
  creatingFromContext: boolean;
  creationProgress: string;

  /* active workspace */
  activeProjectId: string | null;
  activeScenarioId: string | null;
  scenarioState: CanonicalState | null;
  openProject: (projectId: string, scenarioId: string) => Promise<void>;
  refreshScenario: () => Promise<void>;
  submitIntake: (answers: IntakeAnswer[]) => Promise<void>;

  /* run */
  runId: string | null;
  runStatus: string;
  agentStatuses: AgentStatus[];
  events: RunEvent[];
  sseUnsub: (() => void) | null;
  startRun: () => Promise<void>;
  resumeRun: () => Promise<void>;

  /* graph data (derived from scenarioState) */
  nodes: GraphNode[];
  groups: GraphGroup[];

  /* detail drawer */
  selectedNodeId: string | null;
  selectNode: (id: string | null) => void;

  /* chat intake */
  chatMessages: ChatMessage[];
  chatField: string | null;
  chatSuggestions: string[];
  chatReadiness: number;
  chatLoading: boolean;
  sendChatMessage: (message: string) => Promise<void>;
  initChat: () => Promise<void>;

  /* errors */
  error: string | null;
  clearError: () => void;
}

const AGENT_NAMES = [
  "evidence_collector",
  "competitive_teardown_agent",
  "icp_agent",
  "positioning_agent",
  "pricing_agent",
  "channel_strategy_agent",
  "sales_motion_agent",
  "product_strategy_agent",
  "tech_architecture_agent",
  "people_cash_agent",
  "execution_agent",
  "graph_builder",
  "validator_agent",
];

const defaultAgentStatuses = (): AgentStatus[] =>
  AGENT_NAMES.map((name) => ({ name, status: "pending" }));

export const useAppStore = create<AppState>((set, get) => ({
  screen: "home",
  setScreen: (s) => set({ screen: s }),

  projects: [],
  loadProjects: async () => {
    try {
      const projects = await api.listProjects();
      set({ projects, error: null });
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },

  createProject: async (payload) => {
    try {
      const res = await api.createProject(payload);
      set((s) => ({ projects: [...s.projects, res.project], error: null }));
      await get().openProject(res.project.id, res.scenario.id);
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },

  createFromContext: async (context, projectName) => {
    const messages = [
      "Analyzing your idea...",
      "Identifying target market...",
      "Mapping competitive landscape...",
      "Structuring constraints...",
      "Preparing your workspace...",
    ];
    let idx = 0;
    set({ creatingFromContext: true, creationProgress: messages[0], error: null });

    const interval = setInterval(() => {
      idx = (idx + 1) % messages.length;
      set({ creationProgress: messages[idx] });
    }, 2000);

    try {
      const res = await api.createProjectFromContext({ context, project_name: projectName });
      clearInterval(interval);
      set((s) => ({
        projects: [...s.projects, res.project],
        creatingFromContext: false,
        creationProgress: "",
      }));
      await get().openProject(res.project.id, res.scenario.id);
    } catch (e) {
      clearInterval(interval);
      set({ error: (e as Error).message, creatingFromContext: false, creationProgress: "" });
    }
  },

  creatingFromContext: false,
  creationProgress: "",

  activeProjectId: null,
  activeScenarioId: null,
  scenarioState: null,

  openProject: async (projectId, scenarioId) => {
    try {
      const detail = await api.getScenario(scenarioId);
      const screen = needsIntake(detail.state) ? "chat" : "workspace";
      set({
        activeProjectId: projectId,
        activeScenarioId: scenarioId,
        scenarioState: detail.state,
        nodes: detail.state.graph?.nodes ?? [],
        groups: detail.state.graph?.groups ?? [],
        screen,
        runId: null,
        runStatus: "idle",
        agentStatuses: defaultAgentStatuses(),
        events: [],
        error: null,
      });
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },

  refreshScenario: async () => {
    const sid = get().activeScenarioId;
    if (!sid) return;
    try {
      const detail = await api.getScenario(sid);
      set({
        scenarioState: detail.state,
        nodes: detail.state.graph?.nodes ?? [],
        groups: detail.state.graph?.groups ?? [],
      });
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },

  submitIntake: async (answers) => {
    const sid = get().activeScenarioId;
    if (!sid) return;
    try {
      await api.submitIntake(sid, answers);
      await get().refreshScenario();
      set({ screen: "workspace", error: null });
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },

  runId: null,
  runStatus: "idle",
  agentStatuses: defaultAgentStatuses(),
  events: [],
  sseUnsub: null,

  startRun: async () => {
    const sid = get().activeScenarioId;
    if (!sid) return;
    set({ runStatus: "starting", agentStatuses: defaultAgentStatuses(), events: [], error: null });
    try {
      const res = await api.startRun(sid);
      set({ runId: res.run_id, runStatus: res.status });

      // Subscribe to SSE
      const unsub = subscribeToRun(res.run_id, (event) => {
        const state = get();
        set({ events: [...state.events, event] });

        if (event.type === "agent_started") {
          const agentName = event.data.agent as string;
          set({
            agentStatuses: state.agentStatuses.map((a) =>
              a.name === agentName ? { ...a, status: "running" } : a
            ),
          });
        }
        if (event.type === "agent_completed") {
          const agentName = event.data.agent as string;
          set({
            agentStatuses: get().agentStatuses.map((a) =>
              a.name === agentName ? { ...a, status: "completed" } : a
            ),
          });
        }
        if (event.type === "agent_progress") {
          const agentName = event.data.agent as string;
          const patchCount = event.data.patch_count as number;
          set({
            agentStatuses: get().agentStatuses.map((a) =>
              a.name === agentName ? { ...a, patchCount } : a
            ),
          });
        }
        if (event.type === "run_completed") {
          set({ runStatus: "completed" });
          get().refreshScenario().then(() => {
            set({ screen: "decisions" });
          });
        }
        if (event.type === "run_blocked") {
          set({ runStatus: "blocked" });
          get().refreshScenario();
        }
        if (event.type === "run_failed") {
          const failedAgent = event.data.failed_agent as string | undefined;
          set({
            runStatus: "failed",
            agentStatuses: get().agentStatuses.map((a) =>
              a.name === failedAgent ? { ...a, status: "failed" } : a
            ),
          });
        }
      });

      if (get().sseUnsub) get().sseUnsub!();
      set({ sseUnsub: unsub });
    } catch (e) {
      set({ error: (e as Error).message, runStatus: "failed" });
    }
  },

  resumeRun: async () => {
    const rid = get().runId;
    if (!rid) return;
    try {
      const res = await api.resumeRun(rid);
      set({ runId: res.run_id, runStatus: res.status });
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },

  nodes: [],
  groups: [],

  selectedNodeId: null,
  selectNode: (id) => set({ selectedNodeId: id }),

  chatMessages: [],
  chatField: null,
  chatSuggestions: [],
  chatReadiness: 0,
  chatLoading: false,

  initChat: async () => {
    const sid = get().activeScenarioId;
    if (!sid) return;
    if (get().chatMessages.length > 0) return;
    set({ chatLoading: true });
    try {
      // Send an empty-ish greeting to get the first AI question
      const res = await api.sendChat(sid, "Hi, I'm ready to get started.");
      set({
        chatMessages: [
          { role: "user", content: "Hi, I'm ready to get started." },
          { role: "assistant", content: res.message, field: res.field_being_asked ?? undefined, suggestions: res.suggestions },
        ],
        chatField: res.field_being_asked,
        chatSuggestions: res.suggestions,
        chatReadiness: res.readiness,
        chatLoading: false,
      });
    } catch (e) {
      set({ chatLoading: false, error: (e as Error).message });
    }
  },

  sendChatMessage: async (message) => {
    const sid = get().activeScenarioId;
    if (!sid) return;
    const userMsg: ChatMessage = { role: "user", content: message };
    set((s) => ({ chatMessages: [...s.chatMessages, userMsg], chatLoading: true }));
    try {
      const res = await api.sendChat(sid, message, get().chatField ?? undefined);
      const aiMsg: ChatMessage = {
        role: "assistant",
        content: res.message,
        field: res.field_being_asked ?? undefined,
        suggestions: res.suggestions,
      };
      set((s) => ({
        chatMessages: [...s.chatMessages, aiMsg],
        chatField: res.field_being_asked,
        chatSuggestions: res.suggestions,
        chatReadiness: res.readiness,
        chatLoading: false,
      }));
      if (res.ready) {
        // All fields collected — submit intake and transition
        await get().refreshScenario();
        set({ screen: "workspace" });
      }
    } catch (e) {
      set({ chatLoading: false, error: (e as Error).message });
    }
  },

  error: null,
  clearError: () => set({ error: null }),
}));
