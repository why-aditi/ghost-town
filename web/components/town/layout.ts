// World geometry — ported 1:1 from the old SVG viewBox (1000×640) so all
// coordinates transfer directly. World units; the canvas scales to fit.
export const WORLD_W = 1000;
export const WORLD_H = 640;

export type Kind = "house" | "well" | "farm" | "forge" | "market" | "green";
export type Zone = {
  x: number; y: number;      // building anchor (top-center of the structure)
  gx: number; gy: number;    // gathering point (where residents cluster)
  roof: string; kind: Kind;
};

export const Z: Record<string, Zone> = {
  homes:  { x: 190, y: 150, gx: 296, gy: 258, roof: "#b8543f", kind: "house" },
  bakery: { x: 500, y: 116, gx: 500, gy: 232, roof: "#d59a3c", kind: "house" },
  cafe:   { x: 812, y: 150, gx: 706, gy: 258, roof: "#c2683f", kind: "house" },
  well:   { x: 120, y: 330, gx: 258, gy: 384, roof: "#5a6b7a", kind: "well" },
  market: { x: 882, y: 330, gx: 744, gy: 384, roof: "#3f9a6b", kind: "market" },
  farm:   { x: 206, y: 512, gx: 320, gy: 468, roof: "#8a6d3b", kind: "farm" },
  forge:  { x: 794, y: 512, gx: 680, gy: 468, roof: "#4a5568", kind: "forge" },
  square: { x: 500, y: 330, gx: 500, gy: 406, roof: "", kind: "green" },
};

export const PLAZA = { x: 500, y: 335, rx: 150, ry: 120 };
export const CENTER = { x: 500, y: 330 };
export const FOUNTAIN = { x: 500, y: 296 };

// per-agent tunic colors (stable by index, matching the old map)
export const PALETTE = ["#e05a4d", "#e0a63c", "#4fae6d", "#4f92d6",
                        "#a172d6", "#dd6fa8", "#3fb0a5", "#8fbc42"];

// Deterministic cluster slot for agent index `i` of `count` at a zone.
// deterministic 0..1 hash so each agent keeps a stable personal offset
const jitter = (n: number) => {
  const s = Math.sin(n * 127.1) * 43758.5453;
  return s - Math.floor(s);
};

export function slotFor(zone: string, i: number, count: number): { x: number; y: number } {
  const g = Z[zone] ?? Z.square;
  const per = zone === "square" ? 4 : 3;         // the square is roomy; buildings tighter
  const cols = Math.min(count, per);
  const col = i % per, row = Math.floor(i / per);
  const stagger = (row % 2) * 26;                // brick-offset alternate rows
  const jx = (jitter(i * 7 + 1) - 0.5) * 14;     // organic scatter, stable per agent
  const jy = (jitter(i * 7 + 4) - 0.5) * 12;
  return {
    x: g.gx + (col - (cols - 1) / 2) * 52 + stagger - 13 + jx,
    y: g.gy + row * 48 + jy,
  };
}

// Waypoints from a live position to a target slot. Cross-zone walks route
// through the plaza center so residents follow the paths, not diagonals.
export function route(fromX: number, fromY: number, to: { x: number; y: number },
                     sameZone: boolean): { x: number; y: number }[] {
  return sameZone ? [to] : [{ x: CENTER.x, y: CENTER.y }, to];
}
