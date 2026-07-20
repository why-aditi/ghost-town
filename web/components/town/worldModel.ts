// Mutable render-world the animation loop reads/writes, bridged from React
// props via syncFromState (diffs positions to start walks).
import { State } from "@/lib/api";
import { PALETTE, route, slotFor } from "./layout";

export type Wanderer = {
  id: string; name: string; occupation: string; tunic: string;
  x: number; y: number; facing: number;
  tx: number; ty: number;          // current target slot
  zone: string;
  path: { x: number; y: number }[];
  walking: boolean; walkPhase: number; bobPhase: number;
};

export type World = { agents: Map<string, Wanderer>; slot: string; conversations: State["conversations"] };

export function createWorld(): World {
  return { agents: new Map(), slot: "morning", conversations: [] };
}

const REDUCED = typeof window !== "undefined"
  && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

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
        x: slot.x, y: slot.y, facing: 1, tx: slot.x, ty: slot.y, zone: a.position,
        path: [], walking: false, walkPhase: 0, bobPhase: (list.indexOf(a.id) % 6) * 0.4,
      };
      w.agents.set(a.id, ag);
      return;
    }
    const zoneChanged = ag.zone !== a.position;
    const slotChanged = ag.tx !== slot.x || ag.ty !== slot.y;
    if (zoneChanged || slotChanged) {
      if (REDUCED) { ag.x = slot.x; ag.y = slot.y; ag.path = []; ag.walking = false; }
      else { ag.path = route(ag.x, ag.y, slot, !zoneChanged); ag.walking = true; }
    }
    ag.zone = a.position; ag.tx = slot.x; ag.ty = slot.y;
  });
}

const SPEED = 240; // world px / second

export function step(w: World, dt: number) {
  const s = SPEED * (dt / 1000);
  w.agents.forEach((ag) => {
    if (!ag.walking || !ag.path.length) { ag.walking = false; return; }
    let move = s;
    while (move > 0 && ag.path.length) {
      const t = ag.path[0];
      const dx = t.x - ag.x, dy = t.y - ag.y, d = Math.hypot(dx, dy);
      if (d <= move) { ag.x = t.x; ag.y = t.y; ag.path.shift(); move -= d; }
      else { ag.x += (dx / d) * move; ag.y += (dy / d) * move; if (dx) ag.facing = dx < 0 ? -1 : 1; move = 0; }
    }
    if (!ag.path.length) ag.walking = false;
    ag.walkPhase += dt / 1000;
  });
}

export const reducedMotion = REDUCED;
