"use client";

import { useAppStore } from "@/lib/store";
import { Loader2 } from "lucide-react";

export function CreationProgress() {
  const progress = useAppStore((s) => s.creationProgress);

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-[#faf8f3]">
      <div className="text-center space-y-6">
        <Loader2
          size={32}
          strokeWidth={1.5}
          className="mx-auto animate-spin text-sage"
        />
        <p
          key={progress}
          className="text-lg font-medium text-ink animate-fade-in"
        >
          {progress}
        </p>
        <p className="text-xs text-graphite">
          This usually takes a few seconds
        </p>
      </div>
    </div>
  );
}
