// Floating mood/gossip emoji over a sprite. Pure function of (agent, now):
// each agent's emote rises + fades on a staggered loop so the town reads as
// emotionally alive without any per-frame state. reducedMotion hides them.
import type { Wanderer } from "./worldModel";
import { reducedMotion } from "./worldModel";

const PERIOD = 5200; // ms between an agent's emotes
const DUR = 2200;    // ms an emote is visible within the period

const hash = (s: string) => { let h = 0; for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0; return h; };

export function emoteFor(ag: Wanderer, now: number): { emoji: string; phase: number } | null {
  if (reducedMotion) return null;
  const emoji = ag.emote || ag.mood;   // this-tick emote (gossip) overrides the standing mood
  if (!emoji) return null;
  const t = (now + (Math.abs(hash(ag.id)) % PERIOD)) % PERIOD;
  if (t > DUR) return null;
  return { emoji, phase: t / DUR };    // 0 = just appeared, 1 = faded out
}
