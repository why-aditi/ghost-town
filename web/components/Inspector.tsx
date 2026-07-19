"use client";
import { AgentDetail } from "@/lib/api";

const typeColor: Record<string, string> = {
  observation: "bg-zinc-700",
  conversation: "bg-sky-800",
  reflection: "bg-amber-700",
};

function RelBar({ sentiment }: { sentiment: number }) {
  const pct = Math.abs(sentiment) * 50;
  const pos = sentiment >= 0;
  return (
    <div className="relative h-2 w-full rounded bg-zinc-800">
      <div className="absolute top-0 h-2 w-px bg-zinc-600 left-1/2" />
      <div className={`absolute top-0 h-2 ${pos ? "bg-emerald-500" : "bg-red-500"}`}
        style={{ left: pos ? "50%" : `${50 - pct}%`, width: `${pct}%` }} />
    </div>
  );
}

export default function Inspector({
  agent, onClose,
}: { agent: AgentDetail; onClose: () => void }) {
  return (
    <aside className="fixed right-0 top-0 z-20 h-full w-[380px] overflow-y-auto
      border-l border-zinc-800 bg-zinc-900/95 p-5 backdrop-blur shadow-2xl">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-xl font-semibold text-zinc-100">{agent.name}</h2>
          <p className="text-sm text-zinc-400">{agent.occupation} · in the {agent.position}</p>
        </div>
        <button onClick={onClose}
          className="rounded px-2 py-1 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100">✕</button>
      </div>

      <p className="mt-2 text-xs text-zinc-500">{agent.traits.join(" · ")}</p>

      {agent.plan && (
        <section className="mt-5">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-500">Current plan</h3>
          <div className="mt-1 rounded-lg border border-zinc-800 bg-zinc-950 p-3 text-sm">
            <span className="text-emerald-400">→ {agent.plan.destination}</span>{" "}
            <span className="text-zinc-500">[{agent.plan.action}]</span>
            <p className="mt-1 text-zinc-300 italic">“{agent.plan.reason}”</p>
          </div>
        </section>
      )}

      <section className="mt-5">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
          Memories <span className="text-zinc-600">(most important)</span>
        </h3>
        <ul className="mt-1 space-y-1.5">
          {agent.memories.map((m, i) => (
            <li key={i} className="flex gap-2 text-sm">
              <span className={`mt-0.5 shrink-0 rounded px-1.5 text-[10px] uppercase
                leading-4 text-zinc-200 ${typeColor[m.type] || "bg-zinc-700"}`}>
                {m.type[0]}{m.importance}
              </span>
              <span className="text-zinc-300">{m.text}</span>
            </li>
          ))}
          {agent.memories.length === 0 && <li className="text-sm text-zinc-600">no memories yet</li>}
        </ul>
      </section>

      <section className="mt-5">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-500">Relationships</h3>
        <ul className="mt-2 space-y-2.5">
          {agent.relationships.map((r) => (
            <li key={r.other_id} className="text-sm">
              <div className="flex justify-between">
                <span className="text-zinc-300 capitalize">{r.other_id}</span>
                <span className="text-zinc-500">{r.sentiment.toFixed(2)}</span>
              </div>
              <RelBar sentiment={r.sentiment} />
              <p className="mt-0.5 text-xs text-zinc-500 italic">{r.summary}</p>
            </li>
          ))}
          {agent.relationships.length === 0 && <li className="text-sm text-zinc-600">no opinions yet</li>}
        </ul>
      </section>
    </aside>
  );
}
