"use client";
import { Agent, State } from "@/lib/api";

// 8 zones laid out 4×2. viewBox units.
const COLS = 4;
const CW = 210, CH = 205, PAD = 14;
const VW = COLS * CW + PAD;
const zonePos = (i: number) => ({
  x: (i % COLS) * CW + PAD,
  y: Math.floor(i / COLS) * CH + PAD,
  w: CW - PAD,
  h: CH - PAD,
});

// Stable color per agent id.
const PALETTE = ["#f87171", "#fbbf24", "#34d399", "#60a5fa", "#c084fc",
                 "#f472b6", "#2dd4bf", "#a3e635"];
const colorFor = (id: string, agents: Agent[]) =>
  PALETTE[agents.findIndex((a) => a.id === id) % PALETTE.length];

export default function TownMap({
  state, selected, onSelect,
}: { state: State; selected: string | null; onSelect: (id: string) => void }) {
  const zoneIndex = Object.fromEntries(state.zones.map((z, i) => [z, i]));

  // group agents by zone -> position each within its cell
  const byZone: Record<string, Agent[]> = {};
  for (const a of state.agents) (byZone[a.position] ||= []).push(a);
  const coords: Record<string, { x: number; y: number }> = {};
  for (const [zone, list] of Object.entries(byZone)) {
    const p = zonePos(zoneIndex[zone] ?? 0);
    list.forEach((a, i) => {
      coords[a.id] = {
        x: p.x + 40 + (i % 3) * 58,
        y: p.y + 74 + Math.floor(i / 3) * 52,
      };
    });
  }

  // zones with an active conversation (both agents share a zone)
  const talkingZones = new Set(
    state.conversations
      .map(([a]) => state.agents.find((x) => x.id === a)?.position)
      .filter(Boolean) as string[]
  );

  return (
    <svg viewBox={`0 0 ${VW} ${2 * CH + PAD}`} className="w-full h-auto select-none">
      {state.zones.map((zone, i) => {
        const p = zonePos(i);
        return (
          <g key={zone}>
            <rect x={p.x} y={p.y} width={p.w} height={p.h} rx={12}
              fill="#18181b" stroke="#27272a" strokeWidth={1.5} />
            <text x={p.x + 14} y={p.y + 26} fill="#71717a" fontSize={15}
              fontWeight={600} letterSpacing={0.5}>
              {zone}
            </text>
            {talkingZones.has(zone) && (
              <text x={p.x + p.w - 30} y={p.y + 28} fontSize={20}>💬</text>
            )}
          </g>
        );
      })}

      {state.agents.map((a) => {
        const c = coords[a.id];
        if (!c) return null;
        const isSel = a.id === selected;
        return (
          <g key={a.id} onClick={() => onSelect(a.id)}
            style={{ transform: `translate(${c.x}px, ${c.y}px)`,
                     transition: "transform 0.6s ease", cursor: "pointer" }}>
            <circle r={17} fill={colorFor(a.id, state.agents)}
              stroke={isSel ? "#fff" : "#09090b"} strokeWidth={isSel ? 3 : 2} />
            <text textAnchor="middle" dy={5} fontSize={15} fontWeight={700}
              fill="#09090b">{a.name[0]}</text>
            <title>{a.name} — {a.occupation}</title>
          </g>
        );
      })}
    </svg>
  );
}
