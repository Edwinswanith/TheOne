"use client";

import { useCallback, useRef, useState } from "react";

export type SpeechState = "idle" | "listening" | "processing" | "error";

/**
 * Browser-native Speech-to-Text using the Web Speech API.
 * Works in Chrome/Edge/Safari without any backend or API key.
 * Falls back gracefully if the browser doesn't support it.
 */
export function useSpeechInput(onTranscript: (text: string) => void) {
  const [state, setState] = useState<SpeechState>("idle");
  const [interim, setInterim] = useState("");
  const [elapsedMs, setElapsedMs] = useState(0);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = useRef<number>(0);

  const supported = typeof window !== "undefined" && ("SpeechRecognition" in window || "webkitSpeechRecognition" in window);

  const stop = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const start = useCallback(() => {
    if (!supported) {
      setState("error");
      setTimeout(() => setState("idle"), 3000);
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = true;
    recognition.continuous = true;
    recognition.maxAlternatives = 1;

    let finalTranscript = "";

    recognition.onstart = () => {
      setState("listening");
      setInterim("");
      setElapsedMs(0);
      startTimeRef.current = Date.now();
      timerRef.current = setInterval(() => {
        setElapsedMs(Date.now() - startTimeRef.current);
      }, 100);
    };

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let interimText = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript;
        } else {
          interimText += transcript;
        }
      }
      setInterim(interimText);
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      // "aborted" happens on manual stop — not an error
      if (event.error === "aborted") return;
      setState("error");
      setTimeout(() => setState("idle"), 3000);
    };

    recognition.onend = () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      recognitionRef.current = null;
      setInterim("");
      if (finalTranscript.trim()) {
        setState("processing");
        // Small delay to show the "processing" state visually
        setTimeout(() => {
          onTranscript(finalTranscript.trim());
          setState("idle");
        }, 300);
      } else {
        setState("idle");
      }
    };

    recognitionRef.current = recognition;
    recognition.start();
  }, [supported, onTranscript]);

  const toggle = useCallback(() => {
    if (state === "listening") {
      stop();
    } else if (state === "idle") {
      start();
    }
  }, [state, start, stop]);

  const formattedTime = `${Math.floor(elapsedMs / 60000)}:${String(Math.floor((elapsedMs % 60000) / 1000)).padStart(2, "0")}`;

  return { state, interim, elapsed: formattedTime, toggle, supported };
}
