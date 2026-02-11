import React, { useRef, useCallback } from "react";
import { Mic, MicOff, Loader2, AlertCircle } from "lucide-react";
import { useVoiceInput, type VoiceState } from "@/hooks/use-voice-input";

/* ── MicButton ──────────────────────────────────────────────── */

function MicButton({ fieldRef }: { fieldRef: React.RefObject<HTMLInputElement | HTMLTextAreaElement | null> }) {
  const onTranscript = useCallback(
    (text: string) => {
      const el = fieldRef.current;
      if (!el) return;
      const prev = el.value;
      el.value = prev ? `${prev} ${text}` : text;
      // Fire native input event so FormData picks up the value
      el.dispatchEvent(new Event("input", { bubbles: true }));
    },
    [fieldRef],
  );

  const { state, toggle } = useVoiceInput(onTranscript);

  return (
    <button
      type="button"
      onClick={toggle}
      disabled={state === "transcribing"}
      aria-label={state === "recording" ? "Stop recording" : "Start voice input"}
      className={`absolute right-2 top-1/2 -translate-y-1/2 flex h-7 w-7 items-center justify-center rounded-full transition-colors ${stateStyles(state)}`}
    >
      <StateIcon state={state} />
    </button>
  );
}

function stateStyles(s: VoiceState): string {
  switch (s) {
    case "idle":
      return "text-stone-400 hover:text-sage hover:bg-sage/10";
    case "recording":
      return "text-red-500 bg-red-50 animate-pulse";
    case "transcribing":
      return "text-sage";
    case "error":
      return "text-amber-500";
  }
}

function StateIcon({ state }: { state: VoiceState }) {
  switch (state) {
    case "idle":
      return <Mic size={14} strokeWidth={1.5} />;
    case "recording":
      return <MicOff size={14} strokeWidth={1.5} />;
    case "transcribing":
      return <Loader2 size={14} strokeWidth={1.5} className="animate-spin" />;
    case "error":
      return <AlertCircle size={14} strokeWidth={1.5} />;
  }
}

/* ── Input ───────────────────────────────────────────────────── */

export function Input({
  name, label, voiceEnabled, ...props
}: { name: string; label: string; voiceEnabled?: boolean } & React.InputHTMLAttributes<HTMLInputElement>) {
  const ref = useRef<HTMLInputElement>(null);
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-ink">{label}</span>
      <div className="relative">
        <input
          ref={ref}
          name={name}
          {...props}
          className={`w-full sketch-rounded border border-stone-300 bg-white px-3 py-2 text-sm text-ink placeholder:text-stone-400 transition-colors focus:border-sage focus:outline-none focus:ring-2 focus:ring-sage/20 ${voiceEnabled ? "pr-9" : ""}`}
        />
        {voiceEnabled && <MicButton fieldRef={ref} />}
      </div>
    </label>
  );
}

/* ── TextArea ────────────────────────────────────────────────── */

export function TextArea({
  name, label, voiceEnabled, ...props
}: { name: string; label: string; voiceEnabled?: boolean } & React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  const ref = useRef<HTMLTextAreaElement>(null);
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-ink">{label}</span>
      <div className="relative">
        <textarea
          ref={ref}
          name={name}
          rows={2}
          {...props}
          className={`w-full sketch-rounded border border-stone-300 bg-white px-3 py-2 text-sm text-ink placeholder:text-stone-400 transition-colors focus:border-sage focus:outline-none focus:ring-2 focus:ring-sage/20 resize-none ${voiceEnabled ? "pr-9" : ""}`}
        />
        {voiceEnabled && <MicButtonTextArea fieldRef={ref} />}
      </div>
    </label>
  );
}

/* TextArea mic — positioned top-right instead of vertically centered */
function MicButtonTextArea({ fieldRef }: { fieldRef: React.RefObject<HTMLTextAreaElement | null> }) {
  const onTranscript = useCallback(
    (text: string) => {
      const el = fieldRef.current;
      if (!el) return;
      const prev = el.value;
      el.value = prev ? `${prev} ${text}` : text;
      el.dispatchEvent(new Event("input", { bubbles: true }));
    },
    [fieldRef],
  );

  const { state, toggle } = useVoiceInput(onTranscript);

  return (
    <button
      type="button"
      onClick={toggle}
      disabled={state === "transcribing"}
      aria-label={state === "recording" ? "Stop recording" : "Start voice input"}
      className={`absolute right-2 top-2 flex h-7 w-7 items-center justify-center rounded-full transition-colors ${stateStyles(state)}`}
    >
      <StateIcon state={state} />
    </button>
  );
}

/* ── Select ──────────────────────────────────────────────────── */

export function Select({
  name, label, options,
}: { name: string; label: string; options: { value: string; label: string }[] }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-ink">{label}</span>
      <select
        name={name}
        className="w-full sketch-rounded border border-stone-300 bg-white px-3 py-2 text-sm text-ink transition-colors focus:border-sage focus:outline-none focus:ring-2 focus:ring-sage/20"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </label>
  );
}
