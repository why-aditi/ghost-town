"use client";
import { Agent, Conversation } from "@/lib/api";

const PALETTE = ["#e05a4d", "#e0a63c", "#4fae6d", "#4f92d6", "#a172d6",
                 "#dd6fa8", "#3fb0a5", "#8fbc42"];

export default function ConversationDialog({
  convo, agents, onClose,
}: { convo: Conversation; agents: Agent[]; onClose: () => void }) {
  const info = (id: string) => {
    const idx = agents.findIndex((x) => x.id === id);
    return { name: agents[idx]?.name || id, color: PALETTE[idx % PALETTE.length] };
  };
  const A = info(convo.a), B = info(convo.b);

  // "speaker: line" -> { name, text, mine } ; match speaker to A or B loosely
  const turns = convo.lines.map((raw) => {
    const i = raw.indexOf(":");
    const spk = (i > 0 ? raw.slice(0, i) : "").trim().toLowerCase();
    const text = i > 0 ? raw.slice(i + 1).trim() : raw;
    const isB = spk === convo.b || spk === B.name.toLowerCase();
    return { who: isB ? B : A, text, right: isB };
  });

  const learned = Object.entries(convo.transfers).flatMap(([id, facts]) =>
    facts.map((f) => ({ name: info(id).name, fact: f })));

  return (
    <div className="fixed inset-0 z-30 grid place-items-center bg-black/60 p-4" onClick={onClose}>
      <div className="pop w-full max-w-md overflow-hidden rounded-2xl border border-amber-900/50
        bg-[#211c15] shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between border-b border-amber-950/60 px-5 py-3">
          <div>
            <h3 className="font-display text-lg text-amber-100">
              <span style={{ color: A.color }}>{A.name}</span>
              <span className="text-amber-200/40"> & </span>
              <span style={{ color: B.color }}>{B.name}</span>
            </h3>
            <p className="font-hand text-sm text-amber-300/70">in the {convo.zone}</p>
          </div>
          <button onClick={onClose} className="rounded px-2 py-1 text-amber-200/50 hover:bg-black/30 hover:text-amber-100">✕</button>
        </div>

        <div className="max-h-[50vh] space-y-2.5 overflow-y-auto px-5 py-4">
          {turns.length === 0 && <p className="font-serif italic text-amber-100/40">…they spoke, but the words are lost to the wind.</p>}
          {turns.map((t, i) => (
            <div key={i} className={`flex ${t.right ? "justify-end" : "justify-start"}`}>
              <div className="max-w-[80%]">
                <div className={`text-[11px] text-amber-200/50 ${t.right ? "text-right" : ""}`}>{t.who.name}</div>
                <div className="rounded-2xl px-3 py-1.5 text-sm text-amber-50"
                  style={{ background: t.right ? "#3a2f22" : "#2a2620",
                           borderLeft: t.right ? "" : `3px solid ${t.who.color}`,
                           borderRight: t.right ? `3px solid ${t.who.color}` : "" }}>
                  {t.text}
                </div>
              </div>
            </div>
          ))}
        </div>

        {learned.length > 0 && (
          <div className="border-t border-amber-950/60 bg-black/20 px-5 py-3">
            <p className="font-display mb-1 text-[11px] uppercase tracking-[0.15em] text-amber-200/50">What spread</p>
            {learned.map((l, i) => (
              <p key={i} className="font-hand text-sm text-amber-200">
                🤫 <span className="text-amber-100">{l.name}</span> learned: {l.fact}
              </p>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
