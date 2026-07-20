"use client";
import { useState } from "react";

const PRESETS: { label: string; zone: string; description: string }[] = [
  { label: "🧳 Stranger at the square", zone: "square",
    description: "a stranger arrives at the square asking about the old mine" },
  { label: "🪣 The well runs dry", zone: "well",
    description: "the well runs dry and no water comes up" },
  { label: "🧺 Market day", zone: "market",
    description: "it is market day and traders are calling everyone to the market" },
];

export default function EventBox({
  zones, onInject,
}: { zones: string[]; onInject: (zone: string, description: string) => Promise<void> }) {
  const [zone, setZone] = useState("square");
  const [text, setText] = useState("");
  const [flash, setFlash] = useState<string | null>(null);

  async function fire(z: string, d: string) {
    await onInject(z, d);
    setFlash(d);
    setTimeout(() => setFlash(null), 3500);
  }

  return (
    <div className="border-t border-amber-950/60 bg-[#1c1812] px-4 py-2.5">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-display text-xs font-bold uppercase tracking-[0.15em] text-amber-200/60">
          Town crier
        </span>
        {PRESETS.map((p) => (
          <button key={p.label} onClick={() => fire(p.zone, p.description)}
            className="rounded-full border border-amber-900/60 px-3 py-1 text-xs text-amber-100/85
              hover:border-amber-500 hover:text-amber-200">
            {p.label}
          </button>
        ))}
        <span className="mx-1 h-4 w-px bg-amber-900/50" />
        <select value={zone} onChange={(e) => setZone(e.target.value)}
          className="rounded border border-amber-900/60 bg-black/40 px-2 py-1 text-xs text-amber-100">
          {zones.map((z) => <option key={z} value={z}>{z}</option>)}
        </select>
        <input value={text} onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && text.trim()) { fire(zone, text.trim()); setText(""); } }}
          placeholder="proclaim your own event…"
          className="min-w-[220px] flex-1 rounded border border-amber-900/60 bg-black/40 px-2 py-1
            text-xs text-amber-50 placeholder:text-amber-100/30 focus:border-amber-500 focus:outline-none" />
        <button onClick={() => { if (text.trim()) { fire(zone, text.trim()); setText(""); } }}
          className="rounded border-b-2 border-amber-950 bg-amber-600 px-3 py-1 text-xs font-semibold text-amber-50
            hover:bg-amber-500 active:border-b-0">
          Proclaim
        </button>
      </div>
      {flash && <p className="font-hand mt-1 text-sm text-amber-300">✦ the crier calls: “{flash}”</p>}
    </div>
  );
}
