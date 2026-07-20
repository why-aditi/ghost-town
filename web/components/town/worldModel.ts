// Mutable render-world the animation loop reads/writes, bridged from React
// props via syncFromState (diffs positions to start walks).
import { State } from "@/lib/api";
import { PALETTE, route, slotFor } from "./layout";

export type Dir = "down" | "up" | "left" | "right";

export type Wanderer = {
  id: string; name: string; occupation: string; tunic: string;
  x: number; y: number; facing: number; dir: Dir;
  tx: number; ty: number;          // current target slot
  zone: string;
  path: { x: number; y: number }[];
  walking: boolean; walkPhase: number; bobPhase: number;
  // idle micro-wander: drift around `anchor` (the cluster slot) between ticks
  anchor: { x: number; y: number }; wanderT: number; wanderN: number; wander: boolean;
  mood: string; emote: string;     // floating emoji: emote (this tick) overrides mood
};

export type Critter = {
  kind: "cat" | "chicken" | "bird"; x: number; y: number; tx: number; ty: number;
  facing: number; phase: number; wanderT: number; wanderN: number;
  anchor: { x: number; y: number }; rx: number; ry: number; speed: number; seed: number;
};

export type World = {
  agents: Map<string, Wanderer>; slot: string;
  conversations: State["conversations"]; critters: Critter[];
};

function critter(kind: Critter["kind"], ax: number, ay: number, rx: number, ry: number,
                 speed: number, seed: number): Critter {
  return { kind, x: ax, y: ay, tx: ax, ty: ay, facing: 1, phase: 0, wanderT: seed % 3,
           wanderN: 0, anchor: { x: ax, y: ay }, rx, ry, speed, seed };
}

export function createWorld(): World {
  return {
    agents: new Map(), slot: "morning", conversations: [],
    critters: [critter("cat", 500, 372, 96, 74, 46, 3),
               critter("chicken", 320, 476, 58, 30, 34, 11),
               critter("bird", 500, 150, 260, 90, 96, 23)],
  };
}

const REDUCED = typeof window !== "undefined"
  && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

// deterministic per-agent pseudo-randomness (no Math.random in the rAF loop)
const hash = (s: string) => { let h = 0; for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0; return h; };
const jitter = (n: number) => { const x = Math.sin(n * 127.1) * 43758.5453; return x - Math.floor(x); };
const setDir = (ag: Wanderer, dx: number, dy: number) => {
  if (Math.abs(dx) >= Math.abs(dy)) { ag.dir = dx < 0 ? "left" : "right"; ag.facing = dx < 0 ? -1 : 1; }
  else ag.dir = dy < 0 ? "up" : "down";
};

export function syncFromState(w: World, state: State) {
  w.slot = state.time_slot;
  w.conversations = state.conversations;

  const byZone: Record<string, string[]> = {};
  state.agents.forEach((a) => (byZone[a.position] ||= []).push(a.id));

  state.agents.forEach((a) => {
    const list = byZone[a.position];
    const slot = slotFor(a.position, list.indexOf(a.id), list.length);
    let ag = w.agents.get(a.id);
    if (!ag) {
      ag = {
        id: a.id, name: a.name, occupation: a.occupation,
        tunic: PALETTE[state.agents.findIndex((x) => x.id === a.id) % PALETTE.length],
        x: slot.x, y: slot.y, facing: 1, dir: "down", tx: slot.x, ty: slot.y, zone: a.position,
        path: [], walking: false, walkPhase: 0, bobPhase: (list.indexOf(a.id) % 6) * 0.4,
        anchor: { x: slot.x, y: slot.y }, wanderT: jitter(hash(a.id)) * 4 + 1, wanderN: 0, wander: false,
        mood: a.mood || "", emote: "",
      };
      w.agents.set(a.id, ag);
      return;
    }
    ag.mood = a.mood || "";
    const zoneChanged = ag.zone !== a.position;
    const slotChanged = ag.tx !== slot.x || ag.ty !== slot.y;
    if (zoneChanged || slotChanged) {
      if (REDUCED) { ag.x = slot.x; ag.y = slot.y; ag.path = []; ag.walking = false; }
      else { ag.path = route(ag.x, ag.y, slot, !zoneChanged); ag.walking = true; ag.wander = false; }
    }
    ag.zone = a.position; ag.tx = slot.x; ag.ty = slot.y;
    ag.anchor = { x: slot.x, y: slot.y };
  });

  // gossip participants get a 🤫 emote for this tick (overrides their mood)
  w.agents.forEach((ag) => (ag.emote = ""));
  for (const c of state.conversations) {
    if (!c.gossip) continue;
    const a = w.agents.get(c.a), b = w.agents.get(c.b);
    if (a) a.emote = "🤫";
    if (b) b.emote = "🤫";
  }
}

const SPEED = 240;        // world px / second (tick relocation)
const WANDER_SPEED = 78;  // idle micro-wander stroll

export function step(w: World, dt: number) {
  w.agents.forEach((ag) => {
    if (ag.path.length) {
      let move = (ag.wander ? WANDER_SPEED : SPEED) * (dt / 1000);
      while (move > 0 && ag.path.length) {
        const t = ag.path[0];
        const dx = t.x - ag.x, dy = t.y - ag.y, d = Math.hypot(dx, dy);
        if (d <= move) { ag.x = t.x; ag.y = t.y; ag.path.shift(); move -= d; }
        else { ag.x += (dx / d) * move; ag.y += (dy / d) * move; setDir(ag, dx, dy); move = 0; }
      }
      ag.walking = ag.path.length > 0;
      ag.walkPhase += dt / 1000;
      if (!ag.walking && ag.wander) { ag.wander = false; ag.wanderT = 1.4 + jitter(hash(ag.id) + ag.wanderN * 5) * 3.2; }
      return;
    }
    // idle: mill about near the cluster anchor so the town never freezes
    ag.walking = false;
    ag.dir = "down";
    if (REDUCED) return;
    ag.wanderT -= dt / 1000;
    if (ag.wanderT <= 0) {
      ag.wanderN++;
      const a = jitter(hash(ag.id) + ag.wanderN * 3) * Math.PI * 2;
      const r = 8 + jitter(hash(ag.id) + ag.wanderN * 7) * 22;
      ag.path = [{ x: ag.anchor.x + Math.cos(a) * r, y: ag.anchor.y + Math.sin(a) * r * 0.62 }];
      ag.wander = true;
    }
  });

  // face conversation partners while co-located (and don't fidget away mid-talk)
  for (const c of w.conversations) {
    const a = w.agents.get(c.a), b = w.agents.get(c.b);
    if (!a || !b || a.zone !== c.zone || b.zone !== c.zone) continue;
    if (!a.walking && !b.walking) {
      setDir(a, b.x - a.x, b.y - a.y); setDir(b, a.x - b.x, a.y - b.y);
      a.wanderT = Math.max(a.wanderT, 0.8); b.wanderT = Math.max(b.wanderT, 0.8);
    }
  }

  if (!REDUCED) stepCritters(w, dt);
}

function stepCritters(w: World, dt: number) {
  for (const cr of w.critters) {
    const dx = cr.tx - cr.x, dy = cr.ty - cr.y, d = Math.hypot(dx, dy);
    if (d > 1) {
      const move = Math.min(cr.speed * (dt / 1000), d);
      cr.x += (dx / d) * move; cr.y += (dy / d) * move;
      if (Math.abs(dx) > 0.5) cr.facing = dx < 0 ? -1 : 1;
      cr.phase += dt / 1000;
    } else {
      cr.wanderT -= dt / 1000;
      if (cr.wanderT <= 0) {                       // pick a fresh roam target in the ellipse
        cr.wanderN++;
        const a = jitter(cr.seed + cr.wanderN * 3) * Math.PI * 2;
        const rr = 0.4 + jitter(cr.seed + cr.wanderN * 7) * 0.6;
        cr.tx = cr.anchor.x + Math.cos(a) * cr.rx * rr;
        cr.ty = cr.anchor.y + Math.sin(a) * cr.ry * rr;
        cr.wanderT = cr.kind === "bird" ? 0 : 1 + jitter(cr.seed + cr.wanderN) * 3;
      }
    }
  }
}

export const reducedMotion = REDUCED;
