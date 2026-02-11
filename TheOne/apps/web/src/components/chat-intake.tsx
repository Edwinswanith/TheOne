"use client";

import { useEffect, useRef, useState } from "react";
import { useAppStore } from "@/lib/store";
import { ArrowLeft, ArrowUp, Loader2, MessageCircle } from "lucide-react";

export function ChatIntakeScreen() {
  const scenarioState = useAppStore((s) => s.scenarioState);
  const setScreen = useAppStore((s) => s.setScreen);
  const chatMessages = useAppStore((s) => s.chatMessages);
  const chatSuggestions = useAppStore((s) => s.chatSuggestions);
  const chatReadiness = useAppStore((s) => s.chatReadiness);
  const chatLoading = useAppStore((s) => s.chatLoading);
  const sendChatMessage = useAppStore((s) => s.sendChatMessage);
  const initChat = useAppStore((s) => s.initChat);
  const error = useAppStore((s) => s.error);
  const clearError = useAppStore((s) => s.clearError);

  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const ideaName = scenarioState?.idea?.name ?? "Your Project";
  const readinessPct = Math.round(chatReadiness * 100);

  // Start the conversation on mount
  useEffect(() => {
    initChat();
  }, [initChat]);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  function handleSend() {
    const text = input.trim();
    if (!text || chatLoading) return;
    setInput("");
    sendChatMessage(text);
  }

  function handleSuggestionClick(suggestion: string) {
    if (chatLoading) return;
    sendChatMessage(suggestion);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="flex h-screen flex-col bg-[#faf8f3]">
      {/* Top bar */}
      <div className="flex items-center justify-between border-b border-stone-200 bg-white/90 px-4 py-3">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setScreen("home")}
            className="flex items-center gap-1.5 text-sm text-graphite hover:text-ink transition-colors"
          >
            <ArrowLeft size={14} strokeWidth={1.5} />
            Back
          </button>
          <div className="h-4 w-px bg-stone-200" />
          <h1 className="text-sm font-semibold text-ink font-accent">{ideaName}</h1>
        </div>

        <div className="flex items-center gap-3">
          {/* Readiness meter */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-graphite">Readiness</span>
            <div className="w-24 h-2 rounded-full bg-stone-200 overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${readinessPct}%`,
                  background: readinessPct >= 100 ? "#6d8a73" : readinessPct >= 60 ? "#d58c2f" : "#94a3b8",
                }}
              />
            </div>
            <span className="text-xs font-medium text-ink">{readinessPct}%</span>
          </div>

        </div>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="mx-auto max-w-xl space-y-4">
          {error && (
            <div className="sketch-rounded sketch-border bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
              <button onClick={clearError} className="ml-3 font-medium underline">Dismiss</button>
            </div>
          )}

          {chatMessages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} animate-fade-in`}
            >
              <div
                className={`max-w-[80%] sketch-rounded px-4 py-2.5 text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-white border border-stone-200 text-ink"
                    : "bg-sage/10 border border-sage/20 text-ink"
                }`}
              >
                {msg.role === "assistant" && (
                  <div className="flex items-center gap-1.5 mb-1">
                    <MessageCircle size={12} strokeWidth={1.5} className="text-sage" />
                    <span className="text-[10px] font-semibold text-sage uppercase tracking-wide">GTM Advisor</span>
                  </div>
                )}
                {msg.content}
              </div>
            </div>
          ))}

          {chatLoading && (
            <div className="flex justify-start animate-fade-in">
              <div className="sketch-rounded bg-sage/10 border border-sage/20 px-4 py-2.5">
                <Loader2 size={16} strokeWidth={1.5} className="animate-spin text-sage" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Suggestion chips */}
      {chatSuggestions.length > 0 && !chatLoading && (
        <div className="border-t border-stone-100 bg-white/60 px-4 py-2">
          <div className="mx-auto max-w-xl flex flex-wrap gap-2">
            {chatSuggestions.map((suggestion, idx) => (
              <button
                key={idx}
                onClick={() => handleSuggestionClick(suggestion)}
                className="sketch-rounded border-2 border-dashed border-stone-300 px-3 py-1.5 text-xs text-graphite hover:border-sage hover:text-sage transition-colors"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input bar */}
      <div className="border-t border-stone-200 bg-white px-4 py-3">
        <div className="mx-auto max-w-xl flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your answer..."
            disabled={chatLoading}
            className="flex-1 sketch-rounded border border-stone-300 bg-white px-3 py-2 text-sm text-ink placeholder:text-stone-400 focus:border-sage focus:outline-none focus:ring-2 focus:ring-sage/20 disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || chatLoading}
            className="flex h-9 w-9 items-center justify-center sketch-rounded bg-sage text-white transition-all hover:bg-ink disabled:opacity-40"
          >
            <ArrowUp size={16} strokeWidth={2} />
          </button>
        </div>
      </div>
    </div>
  );
}
