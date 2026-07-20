"use client";
import { AgentDetail } from "@/lib/api";

const typeColor: Record<string, string> = {
  observation: "bg-stone-600",
  conversation: "bg-sky-800",
  reflection: "bg-amber-700",
};

function RelBar({ sentiment }: { sentiment: number }) {
  const pct = Math.abs(sentiment) * 50;
  const pos = sentiment >= 0;
  return (
    <div className="relative h-2 w-full rounded bg-black/40">
      <div className="absolute left-1/2 top-0 h-2 w-px bg-amber-100/20" />
      <div className={`absolute top-0 h-2 ${pos ? "bg-emerald-500" : "bg-rose-500"}`}
        style={{ left: pos ? "50%" : `${50 - pct}%`, width: `${pct}%` }} />
    </div>
  );
}

export default function Inspector({
  agent, onClose,
}: { agent: AgentDetail; onClose: () => void }) {
  return (
    <aside className="pop fixed right-0 top-0 z-20 h-full w-[380px] overflow-y-auto border-l
      border-amber-900/50 bg-[#211c15] p-5 shadow-2xl" style={{ transformOrigin: "right center" }}>
      <div className="flex items-start justify-between">
        <div>
          <h2 className="font-display text-2xl font-bold text-amber-100">{agent.name}</h2>
          <p className="text-sm text-amber-200/60">{agent.occupation} · in the {agent.position}</p>
        </div>
        <button onClick={onClose}
          className="rounded px-2 py-1 text-amber-200/50 hover:bg-black/30 hover:text-amber-100">✕</button>
      </div>

      <p className="font-hand mt-1 text-base text-amber-300/70">{agent.traits.join(" · ")}</p>

      {agent.plan && (
        <section className="mt-5">
          <h3 className="font-display text-xs font-bold uppercase tracking-[0.15em] text-amber-200/50">Right now</h3>
          <div className="mt-1 rounded-lg border border-amber-900/40 bg-black/25 p-3 text-sm">
            <span className="text-emerald-400">→ {agent.plan.destination}</span>{" "}
            <span className="text-amber-200/40">[{agent.plan.action}]</span>
            <p className="font-serif mt-1 text-amber-50/80 italic">“{agent.plan.reason}”</p>
          </div>
        </section>
      )}

      <section className="mt-5">
        <h3 className="font-display text-xs font-bold uppercase tracking-[0.15em] text-amber-200/50">
          Memories <span className="text-amber-200/30">· most important</span>
        </h3>
        <ul className="mt-2 space-y-1.5">
          {agent.memories.map((m, i) => (
            <li key={i} className="flex gap-2 text-sm">
              <span title={`${m.type} · importance ${m.importance}/10`}
                className={`mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded text-[11px]
                  font-semibold leading-none text-amber-50 ${typeColor[m.type] || "bg-stone-600"}`}>
                {m.importance}
              </span>
              <span className="text-amber-50/80">
                <span className="mr-1 text-[10px] uppercase tracking-wide text-amber-200/40">{m.type}</span>
                {m.text}
              </span>
            </li>
          ))}
          {agent.memories.length === 0 && <li className="text-sm text-amber-200/30">no memories yet</li>}
        </ul>
      </section>

      <section className="mt-5">
        <h3 className="font-display text-xs font-bold uppercase tracking-[0.15em] text-amber-200/50">Feelings toward others</h3>
        <ul className="mt-2 space-y-2.5">
          {agent.relationships.map((r) => (
            <li key={r.other_id} className="text-sm">
              <div className="flex justify-between">
                <span className="capitalize text-amber-50/80">{r.other_id}</span>
                <span className="text-amber-200/40">{r.sentiment.toFixed(2)}</span>
              </div>
              <RelBar sentiment={r.sentiment} />
              <p className="font-serif mt-0.5 text-xs italic text-amber-200/40">{r.summary}</p>
            </li>
          ))}
          {agent.relationships.length === 0 && <li className="text-sm text-amber-200/30">no opinions yet</li>}
        </ul>
      </section>
    </aside>
  );
}
