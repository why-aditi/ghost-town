"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import Controls from "@/components/Controls";
import ConversationDialog from "@/components/ConversationDialog";
import EventBox from "@/components/EventBox";
import Inspector from "@/components/Inspector";
import StoryLog from "@/components/StoryLog";
import TownCanvas from "@/components/town/TownCanvas";
import { audio } from "@/components/town/audio";
import {
  AgentDetail, Conversation, State, StoryEntry,
  getAgent, getState, getStory, injectEvent, streamTick,
} from "@/lib/api";

export default function Page() {
  const [state, setState] = useState<State | null>(null);
  const [story, setStory] = useState<StoryEntry[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [agent, setAgent] = useState<AgentDetail | null>(null);
  const [phase, setPhase] = useState<string | null>(null);
  const [autoplay, setAutoplay] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [sound, setSound] = useState(false);
  const [follow, setFollow] = useState(false);
  const [resetNonce, setResetNonce] = useState(0);
  const [dayFade, setDayFade] = useState<number | null>(null);
  const [whisper, setWhisper] = useState<string | null>(null);
  const [convo, setConvo] = useState<Conversation | null>(null);
  const ticking = state?.ticking ?? false;

  const refresh = useCallback(async () => {
    setState(await getState());
    setStory(await getStory());
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  // refresh the open inspector whenever the world changes
  useEffect(() => {
    if (selected) getAgent(selected).then(setAgent);
  }, [selected, state?.tick]);

  // "a day passes" vignette on day rollover
  const prevDay = useRef<number>();
  useEffect(() => {
    if (state && prevDay.current !== undefined && state.day !== prevDay.current) {
      setDayFade(state.day);
      const t = setTimeout(() => setDayFade(null), 1900);
      prevDay.current = state.day;
      return () => clearTimeout(t);
    }
    if (state) prevDay.current = state.day;
  }, [state?.day]);

  // surface a whispered secret when one passes this tick
  useEffect(() => {
    const g = state?.gossip;
    if (g && g.length) {
      setWhisper(g[g.length - 1]);
      const t = setTimeout(() => setWhisper(null), 6000);
      return () => clearTimeout(t);
    }
  }, [state?.tick, state?.gossip]);

  const doTick = useCallback(async () => {
    if (state?.ticking) return;
    setState((s) => (s ? { ...s, ticking: true } : s));
    try {
      await streamTick((ev, data) => setPhase(data.label || ev));
    } catch (e: any) {
      setPhase(`⚠ ${e.message}`);
    } finally {
      setPhase(null);
      await refresh();
    }
  }, [state?.ticking, refresh]);

  // autoplay: sequential — after a tick resolves, wait 3s, tick again
  const autoRef = useRef(autoplay);
  autoRef.current = autoplay;
  useEffect(() => {
    if (!autoplay || ticking) return;
    const t = setTimeout(() => { if (autoRef.current) doTick(); }, 3000 / speed);
    return () => clearTimeout(t);
  }, [autoplay, ticking, doTick, speed]);

  const inject = async (zone: string, description: string) => {
    await injectEvent(zone, description);
  };

  if (!state) {
    return <div className="font-serif grid h-full place-items-center italic text-amber-100/40">
      Waking the town…
    </div>;
  }

  return (
    <main className="flex h-screen flex-col bg-[#17140f]">
      <Controls day={state.day} tick={state.tick} ticking={ticking} phase={phase}
        autoplay={autoplay} onTick={doTick}
        onToggleAutoplay={() => setAutoplay((a) => !a)}
        speed={speed} onCycleSpeed={() => setSpeed((s) => (s === 1 ? 2 : s === 2 ? 4 : 1))}
        sound={sound} onToggleSound={() => setSound(audio.toggle())} />

      <div className="flex min-h-0 flex-1">
        <section className="relative flex min-w-0 flex-1 items-center justify-center p-4">
          <TownCanvas state={state} selected={selected} onSelect={setSelected}
            onConversation={setConvo} follow={follow}
            onFollowEnd={() => setFollow(false)} resetNonce={resetNonce} />
          {whisper && (
            <div className="pop absolute left-1/2 top-5 -translate-x-1/2 rounded-full border
              border-amber-500/50 bg-black/70 px-4 py-1.5 backdrop-blur">
              <span className="font-hand text-lg text-amber-200">🤫 {whisper}</span>
            </div>
          )}
          {dayFade !== null && (
            <div className="dayfade pointer-events-none absolute inset-4 z-20 grid place-items-center rounded-2xl bg-black/70">
              <span className="font-display text-4xl font-bold tracking-wide text-amber-100">Day {dayFade}</span>
            </div>
          )}
          <div className="absolute bottom-5 left-5 flex gap-2">
            <button onClick={() => setResetNonce((n) => n + 1)} title="Reset view"
              className="rounded-lg border border-amber-900/60 bg-black/50 px-2.5 py-1.5 text-sm text-amber-100/85 backdrop-blur hover:bg-black/70">
              ⤢ Reset
            </button>
            <button onClick={() => setFollow((f) => !f)} disabled={!selected} title="Follow selected"
              className={`rounded-lg px-2.5 py-1.5 text-sm backdrop-blur disabled:opacity-30 ${
                follow ? "bg-amber-600 text-amber-50" : "border border-amber-900/60 bg-black/50 text-amber-100/85 hover:bg-black/70"}`}>
              🎯 {follow ? "Following" : "Follow"}
            </button>
          </div>
        </section>
        <section className="w-[32%] min-w-[300px] border-l border-amber-950/60 bg-[#1e1a13] p-5">
          <StoryLog entries={story} />
        </section>
      </div>

      <EventBox zones={state.zones} onInject={inject} />

      {selected && agent && (
        <Inspector agent={agent} onClose={() => { setSelected(null); setAgent(null); setFollow(false); }} />
      )}
      {convo && (
        <ConversationDialog convo={convo} agents={state.agents} onClose={() => setConvo(null)} />
      )}
    </main>
  );
}
