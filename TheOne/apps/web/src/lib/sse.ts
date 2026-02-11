import type { RunEvent } from "@/lib/types";

export function subscribeToRun(runId: string, onEvent: (event: RunEvent) => void) {
  const url = `${process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000"}/runs/${runId}/stream`;
  const source = new EventSource(url);

  source.onmessage = (message) => {
    const event = JSON.parse(message.data) as RunEvent;
    onEvent(event);
  };

  source.onerror = () => {
    source.close();
  };

  return () => source.close();
}
