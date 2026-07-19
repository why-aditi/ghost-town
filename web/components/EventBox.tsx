"use client";
import { useState } from "react";

const PRESETS: { label: string; zone: string; description: string }[] = [
  { label: "Stranger at the square", zone: "square",
    description: "a stranger arrives at the square asking about the old mine" },
  { label: "The well runs dry", zone: "well",
    description: "the well runs dry and no water comes up" },
  { label: "Market day", zone: "market",
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
    setTimeout(() => setFlash(null), 3000);
  }

  return (
    <div className="border-t border-zinc-800 bg-zinc-900/60 px-4 py-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
          Inject event
        </span>
        {PRESETS.map((p) => (
          <button key={p.label} onClick={() => fire(p.zone, p.description)}
            className="rounded-full border border-zinc-700 px-3 py-1 text-xs text-zinc-300
              hover:border-emerald-600 hover:text-emerald-400">
            {p.label}
          </button>
        ))}
        <span className="mx-1 h-4 w-px bg-zinc-700" />
        <select value={zone} onChange={(e) => setZone(e.target.value)}
          className="rounded border border-zinc-700 bg-zinc-950 px-2 py-1 text-xs text-zinc-300">
          {zones.map((z) => <option key={z} value={z}>{z}</option>)}
        </select>
        <input value={text} onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && text.trim()) { fire(zone, text.trim()); setText(""); } }}
          placeholder="free-text event…"
          className="min-w-[220px] flex-1 rounded border border-zinc-700 bg-zinc-950 px-2 py-1
            text-xs text-zinc-200 placeholder:text-zinc-600 focus:border-emerald-600 focus:outline-none" />
        <button onClick={() => { if (text.trim()) { fire(zone, text.trim()); setText(""); } }}
          className="rounded bg-emerald-700 px-3 py-1 text-xs font-medium text-white hover:bg-emerald-600">
          Inject
        </button>
      </div>
      {flash && <p className="mt-1.5 text-xs text-emerald-400">✓ injected: “{flash}”</p>}
    </div>
  );
}
