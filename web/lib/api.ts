// API client for the Ghost Town FastAPI backend.
export const API = process.env.NEXT_PUBLIC_API || "http://127.0.0.1:8000";

export type Agent = { id: string; name: string; occupation: string; position: string; mood?: string };
export type Conversation = {
  a: string; b: string; zone: string; gossip: boolean;
  lines: string[]; transfers: Record<string, string[]>;
};
export type State = {
  tick: number; day: number; time_slot: string; zones: string[];
  agents: Agent[]; conversations: Conversation[]; gossip: string[]; ticking: boolean;
};
export type Memory = { type: string; importance: number; text: string; tick: number };
export type Relationship = { other_id: string; sentiment: number; summary: string };
export type AgentDetail = {
  id: string; name: string; occupation: string; position: string;
  traits: string[]; goals: string[];
  plan: { destination: string; action: string; reason: string } | null;
  memories: Memory[]; relationships: Relationship[];
};
export type StoryEntry = { tick: number; prose: string };

export const getState = () => fetch(`${API}/state`).then((r) => r.json() as Promise<State>);
export const getAgent = (id: string) =>
  fetch(`${API}/agents/${id}`).then((r) => r.json() as Promise<AgentDetail>);
export const getStory = () => fetch(`${API}/story`).then((r) => r.json() as Promise<StoryEntry[]>);
export const injectEvent = (zone: string, description: string) =>
  fetch(`${API}/events`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ zone, description }),
  }).then((r) => r.json());

// POST /tick returns an SSE stream (per-phase progress, then a final report).
// EventSource can't POST, so we read the body and parse SSE frames ourselves.
export async function streamTick(
  onPhase: (event: string, data: any) => void
): Promise<any | null> {
  const res = await fetch(`${API}/tick`, { method: "POST" });
  if (res.status === 409) throw new Error("A tick is already running");
  if (!res.body) throw new Error("No response stream");
  const reader = res.body.getReader();
  const dec = new TextDecoder();
  let buf = "";
  let report: any = null;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    const frames = buf.split("\n\n");
    buf = frames.pop() || "";
    for (const frame of frames) {
      const ev = /^event: (.*)$/m.exec(frame)?.[1];
      const dm = /^data: (.*)$/m.exec(frame);
      if (!ev || !dm) continue; // ": ping" keepalives have no event/data
      const data = JSON.parse(dm[1]);
      if (ev === "report") report = data;
      else if (ev === "error") throw new Error(data.detail || "tick failed");
      else onPhase(ev, data);
    }
  }
  return report;
}
