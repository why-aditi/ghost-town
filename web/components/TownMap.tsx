"use client";
import { Agent, State } from "@/lib/api";

// --- village layout (viewBox 1000×640) -------------------------------------
type Cfg = { x: number; y: number; gx: number; gy: number;
             roof: string; icon: string; kind: "house" | "well" | "farm" | "forge" | "market" | "green" };
const Z: Record<string, Cfg> = {
  homes:  { x: 190, y: 150, gx: 296, gy: 258, roof: "#b8543f", icon: "🏠", kind: "house" },
  bakery: { x: 500, y: 116, gx: 500, gy: 232, roof: "#d59a3c", icon: "🥖", kind: "house" },
  cafe:   { x: 812, y: 150, gx: 706, gy: 258, roof: "#c2683f", icon: "☕", kind: "house" },
  well:   { x: 120, y: 330, gx: 258, gy: 384, roof: "#5a6b7a", icon: "🪣", kind: "well" },
  market: { x: 882, y: 330, gx: 744, gy: 384, roof: "#3f9a6b", icon: "🧺", kind: "market" },
  farm:   { x: 206, y: 512, gx: 320, gy: 468, roof: "#8a6d3b", icon: "🌾", kind: "farm" },
  forge:  { x: 794, y: 512, gx: 680, gy: 468, roof: "#4a5568", icon: "🔨", kind: "forge" },
  square: { x: 500, y: 330, gx: 500, gy: 406, roof: "", icon: "⛲", kind: "green" },
};

const PALETTE = ["#e05a4d", "#e0a63c", "#4fae6d", "#4f92d6", "#a172d6",
                 "#dd6fa8", "#3fb0a5", "#8fbc42"];
const tunic = (id: string, agents: Agent[]) =>
  PALETTE[agents.findIndex((a) => a.id === id) % PALETTE.length];

const SKY: Record<string, string> = { morning: "dawn", afternoon: "day", evening: "dusk" };

function Building({ zone, cfg }: { zone: string; cfg: Cfg }) {
  const { x, y, roof, icon, kind } = cfg;
  const ink = "#4a3f30", wall = "#f0e6d0", shade = "#e2d4b6";
  const sign = (
    <g transform={`translate(${x}, ${y + 66})`}>
      <rect x={-38} y={-2} width={76} height={22} rx={5} fill="#6b4f34" stroke={ink} strokeWidth={1.5} />
      <text x={0} y={14} textAnchor="middle" className="font-hand" fill="#f6ecd6"
        fontSize={17} fontWeight={700}>{zone}</text>
    </g>
  );

  if (kind === "green") return null; // the square is the plaza + fountain

  if (kind === "well")
    return (
      <g>
        <ellipse cx={x} cy={y + 44} rx={34} ry={9} fill="#000" opacity={0.14} />
        <rect x={x - 26} y={y + 6} width={52} height={40} rx={6} fill="#9aa6ad" stroke={ink} strokeWidth={2} />
        <rect x={x - 26} y={y + 6} width={52} height={10} fill={roof} />
        <line x1={x - 20} y1={y + 6} x2={x - 20} y2={y - 20} stroke={ink} strokeWidth={3} />
        <line x1={x + 20} y1={y + 6} x2={x + 20} y2={y - 20} stroke={ink} strokeWidth={3} />
        <polygon points={`${x - 30},${y - 18} ${x + 30},${y - 18} ${x},${y - 40}`} fill={roof} stroke={ink} strokeWidth={2} />
        <text x={x} y={y + 33} textAnchor="middle" fontSize={16}>💧</text>
        {sign}
      </g>
    );

  if (kind === "farm")
    return (
      <g>
        <rect x={x - 46} y={y - 6} width={92} height={52} rx={6} fill="#7c5a34" stroke={ink} strokeWidth={2} />
        {[0, 1, 2, 3].map((i) => (
          <line key={i} x1={x - 40 + i * 26} y1={y - 2} x2={x - 40 + i * 26} y2={y + 42} stroke="#a8f06e" strokeWidth={5} />
        ))}
        {sign}
      </g>
    );

  // house / market / forge share a cottage silhouette, distinguished by roof + icon
  return (
    <g>
      <ellipse cx={x} cy={y + 52} rx={48} ry={11} fill="#000" opacity={0.14} />
      <rect x={x - 42} y={y} width={84} height={54} rx={4} fill={wall} stroke={ink} strokeWidth={2} />
      <rect x={x - 42} y={y + 34} width={84} height={20} fill={shade} />
      <polygon points={`${x - 52},${y + 2} ${x + 52},${y + 2} ${x},${y - 40}`} fill={roof} stroke={ink} strokeWidth={2} />
      {kind === "forge" && <rect x={x + 22} y={y - 38} width={12} height={22} fill="#3a3a3a" stroke={ink} strokeWidth={1.5} />}
      {kind === "market" && <rect x={x - 44} y={y - 6} width={88} height={12} rx={3} fill="#d8604f" />}
      <rect x={x - 10} y={y + 24} width={20} height={30} rx={2} fill="#7c5a34" stroke={ink} strokeWidth={1.5} />
      <rect className="window" x={x - 34} y={y + 12} width={16} height={16} rx={2} fill="#8fb8cf" stroke={ink} strokeWidth={1.5} />
      <rect className="window" x={x + 18} y={y + 12} width={16} height={16} rx={2} fill="#8fb8cf" stroke={ink} strokeWidth={1.5} />
      <text x={x} y={y - 12} textAnchor="middle" fontSize={16}>{icon}</text>
      {sign}
    </g>
  );
}

function Character({ x, y, color, name, selected, delay, onClick }:
  { x: number; y: number; color: string; name: string; selected: boolean; delay: number; onClick: () => void }) {
  const ink = "#4a3f30", skin = "#eab892", hair = "#5a3d28";
  return (
    <g transform={`translate(${x}, ${y})`} onClick={onClick}
      style={{ transition: "transform 0.8s cubic-bezier(.4,0,.2,1)", cursor: "pointer" }}>
      <ellipse cx={0} cy={17} rx={12} ry={3.5} fill="#000" opacity={0.22} />
      {selected && <circle cy={-2} r={22} fill="none" stroke="#ffd27a" strokeWidth={2.5} opacity={0.9} />}
      <g className="bob" style={{ animationDelay: `${delay}s` }}>
        <path d="M-9,15 Q-11,-3 0,-5 Q11,-3 9,15 Z" fill={color} stroke={ink} strokeWidth={1.6} />
        <circle cx={0} cy={-11} r={7} fill={skin} stroke={ink} strokeWidth={1.3} />
        <path d="M-7,-13 Q0,-21 7,-13 Q3,-17 0,-16.5 Q-3,-17 -7,-13 Z" fill={hair} />
      </g>
      <text y={31} textAnchor="middle" className="font-hand" fontSize={13} fontWeight={700}
        fill="#f2e8d4" stroke="#17140f" strokeWidth={0.6} paintOrder="stroke">{name}</text>
      <title>{name}</title>
    </g>
  );
}

export default function TownMap({
  state, selected, onSelect,
}: { state: State; selected: string | null; onSelect: (id: string) => void }) {
  // cluster agents at each zone's gathering point
  const byZone: Record<string, Agent[]> = {};
  for (const a of state.agents) (byZone[a.position] ||= []).push(a);
  const pos: Record<string, { x: number; y: number }> = {};
  for (const [zone, list] of Object.entries(byZone)) {
    const g = Z[zone] || Z.square;
    const cols = Math.min(list.length, 4);
    list.forEach((a, i) => {
      const col = i % 4, row = Math.floor(i / 4);
      pos[a.id] = { x: g.gx + (col - (cols - 1) / 2) * 38, y: g.gy + row * 40 };
    });
  }

  const slot = SKY[state.time_slot] || "day";
  const dusk = state.time_slot === "evening";

  return (
    <svg viewBox="0 0 1000 640" className="h-full w-full select-none" style={{ filter: "drop-shadow(0 8px 24px rgba(0,0,0,.4))" }}>
      <defs>
        <linearGradient id="dawn" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#f6c99f" /><stop offset="1" stopColor="#a9c8d8" />
        </linearGradient>
        <linearGradient id="day" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#bfe0ec" /><stop offset="1" stopColor="#d8ecc4" />
        </linearGradient>
        <linearGradient id="dusk" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#3a2f56" /><stop offset="1" stopColor="#6a5170" />
        </linearGradient>
        <radialGradient id="plaza" cx="0.5" cy="0.5" r="0.6">
          <stop offset="0" stopColor="#a9c078" /><stop offset="1" stopColor="#94ac66" />
        </radialGradient>
        <style>{dusk ? ".window{fill:#ffd27a !important;}" : ""}</style>
      </defs>

      <rect width={1000} height={640} fill={`url(#${slot})`} />
      {/* grass island */}
      <rect x={16} y={16} width={968} height={608} rx={30} fill="#8ba86a" stroke="#6f8a52" strokeWidth={3} />
      {/* decorative bushes/trees */}
      {[[70, 90], [930, 100], [60, 560], [940, 560], [500, 40], [500, 600]].map(([bx, by], i) => (
        <g key={i}><ellipse cx={bx} cy={by + 8} rx={20} ry={6} fill="#000" opacity={0.12} />
          <circle cx={bx} cy={by} r={17} fill="#5f7f43" /><circle cx={bx - 9} cy={by + 4} r={12} fill="#6d8f4d" /><circle cx={bx + 9} cy={by + 3} r={12} fill="#6d8f4d" /></g>
      ))}

      {/* central plaza + paths radiating out */}
      {Object.entries(Z).filter(([z]) => z !== "square").map(([z, c]) => (
        <line key={z} x1={500} y1={330} x2={c.gx} y2={c.gy} stroke="#d9c49a" strokeWidth={20} strokeLinecap="round" opacity={0.9} />
      ))}
      <ellipse cx={500} cy={335} rx={150} ry={120} fill="url(#plaza)" stroke="#7f9757" strokeWidth={2} />

      {/* fountain (the square) */}
      <g>
        <ellipse cx={500} cy={300} rx={40} ry={14} fill="#000" opacity={0.12} />
        <circle cx={500} cy={296} r={34} fill="#b9c2c8" stroke="#4a3f30" strokeWidth={2.5} />
        <circle cx={500} cy={296} r={24} fill="#6bb5d6" stroke="#4a3f30" strokeWidth={1.5} />
        <rect x={497} y={276} width={6} height={20} fill="#9aa6ad" />
        <circle cx={500} cy={274} r={4} fill="#8fd3ec" />
        <g transform="translate(500,282)" fill="#bfe6f6"><ellipse cx={-8} cy={4} rx={2} ry={5} /><ellipse cx={8} cy={4} rx={2} ry={5} /></g>
      </g>

      {/* buildings */}
      {Object.entries(Z).map(([z, c]) => <Building key={z} zone={z} cfg={c} />)}

      {/* conversation bubbles + gossip ripples (drawn under characters' labels) */}
      {state.conversations.map((c, i) => {
        const pa = pos[c.a], pb = pos[c.b];
        if (!pa || !pb) return null;
        const mx = (pa.x + pb.x) / 2, my = Math.min(pa.y, pb.y) - 26;
        return (
          <g key={i} className="pop">
            {c.gossip && <>
              <circle className="ripple" cx={mx} cy={my + 20} fill="none" stroke="#ffcf70" strokeWidth={2} />
              <path className="whisper" d={`M${pa.x},${pa.y - 10} Q${mx},${my - 8} ${pb.x},${pb.y - 10}`}
                fill="none" stroke="#ffd27a" strokeWidth={2.5} />
            </>}
            <g transform={`translate(${mx}, ${my})`}>
              <rect x={-16} y={-14} width={32} height={24} rx={9}
                fill={c.gossip ? "#fff3d6" : "#fbf6ea"} stroke="#4a3f30" strokeWidth={1.5} />
              <polygon points="-4,9 4,9 0,17" fill={c.gossip ? "#fff3d6" : "#fbf6ea"} stroke="#4a3f30" strokeWidth={1.5} />
              <text y={2} textAnchor="middle" fontSize={13}>{c.gossip ? "🤫" : "💬"}</text>
            </g>
          </g>
        );
      })}

      {/* characters */}
      {state.agents.map((a, i) => {
        const p = pos[a.id];
        return p ? (
          <Character key={a.id} x={p.x} y={p.y} name={a.name} color={tunic(a.id, state.agents)}
            selected={a.id === selected} delay={(i % 6) * 0.35} onClick={() => onSelect(a.id)} />
        ) : null;
      })}

      {/* dusk mood: darkening overlay + fireflies */}
      {dusk && <>
        <rect width={1000} height={640} rx={30} fill="#1a1636" opacity={0.28} pointerEvents="none" />
        {[[300, 260], [680, 220], [460, 420], [780, 400], [220, 380]].map(([fx, fy], i) => (
          <circle key={i} className="firefly" cx={fx} cy={fy} r={2.5} fill="#ffe89a"
            style={{ animationDelay: `${i * 0.9}s` }} />
        ))}
      </>}
    </svg>
  );
}
