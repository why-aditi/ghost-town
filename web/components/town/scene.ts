// Static map baked once to an offscreen canvas + live per-frame layers.
import { WORLD_W, WORLD_H, Z, PLAZA, CENTER, FOUNTAIN } from "./layout";

export type Rect = { x: number; y: number; w: number; h: number };

const R = (c: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, col: string) => {
  c.fillStyle = col; c.fillRect(x, y, w, h);
};
const hash = (x: number, y: number) => {
  const n = Math.sin(x * 12.9898 + y * 78.233) * 43758.5453;
  return n - Math.floor(n);
};

const INK = "#4a3f30", WALL = "#f0e6d0", SHADE = "#e2d4b6";

function roof(c: CanvasRenderingContext2D, x: number, y: number, col: string) {
  c.beginPath();
  c.moveTo(x - 52, y + 2); c.lineTo(x + 52, y + 2); c.lineTo(x, y - 40); c.closePath();
  c.fillStyle = col; c.fill();
  c.strokeStyle = INK; c.lineWidth = 2; c.stroke();
}

function building(c: CanvasRenderingContext2D, zone: string, windows: Rect[]) {
  const z = Z[zone]; const { x, y, kind, roof: rc } = z;
  if (kind === "green") return;

  if (kind === "well") {
    R(c, x - 26, y + 6, 52, 40, "#9aa6ad");
    c.strokeStyle = INK; c.lineWidth = 2; c.strokeRect(x - 26, y + 6, 52, 40);
    R(c, x - 26, y + 6, 52, 8, rc);
    R(c, x - 20, y - 20, 3, 26, INK); R(c, x + 17, y - 20, 3, 26, INK);
    roof(c, x, y - 16, rc);
    R(c, x - 10, y + 20, 20, 14, "#5aa9c9");
    return;
  }
  if (kind === "farm") {
    R(c, x - 46, y - 4, 92, 50, "#7c5a34");
    c.strokeStyle = INK; c.lineWidth = 2; c.strokeRect(x - 46, y - 4, 92, 50);
    for (let i = 0; i < 4; i++) R(c, x - 40 + i * 26, y, 6, 42, "#8fd44e");
    // little barn
    R(c, x + 28, y - 22, 26, 22, "#b8543f");
    roof(c, x + 41, y - 22, "#8a3f30");
    return;
  }

  // cottage silhouette (house / market / forge / cafe)
  R(c, x - 42, y, 84, 54, WALL);
  R(c, x - 42, y + 34, 84, 20, SHADE);
  c.strokeStyle = INK; c.lineWidth = 2; c.strokeRect(x - 42, y, 84, 54);
  roof(c, x, y, rc);
  if (kind === "forge") { R(c, x + 22, y - 40, 12, 24, "#3a3a3a"); R(c, x + 20, y - 44, 16, 5, "#555"); }
  if (kind === "market") R(c, x - 44, y - 6, 88, 12, "#d8604f");
  // door + windows (collect windows for evening glow)
  R(c, x - 10, y + 24, 20, 30, "#7c5a34");
  c.strokeStyle = INK; c.strokeRect(x - 10, y + 24, 20, 30);
  for (const wx of [x - 34, x + 18]) {
    const win = { x: wx, y: y + 12, w: 16, h: 16 };
    R(c, win.x, win.y, win.w, win.h, "#8fb8cf");
    c.strokeStyle = INK; c.strokeRect(win.x, win.y, win.w, win.h);
    windows.push(win);
  }
}

function bush(c: CanvasRenderingContext2D, x: number, y: number) {
  R(c, x - 14, y - 4, 28, 12, "#5f7f43");
  R(c, x - 18, y, 12, 10, "#6d8f4d");
  R(c, x + 6, y, 12, 10, "#6d8f4d");
  R(c, x - 6, y - 12, 14, 12, "#6d8f4d");
}

/** Bake the static scene; returns the canvas + window rects for glow. */
export function bakeScene(): { canvas: HTMLCanvasElement; windows: Rect[] } {
  const canvas = document.createElement("canvas");
  canvas.width = WORLD_W; canvas.height = WORLD_H;
  const c = canvas.getContext("2d")!;
  c.imageSmoothingEnabled = false;
  const windows: Rect[] = [];

  // grass island
  c.beginPath();
  (c as any).roundRect(16, 16, WORLD_W - 32, WORLD_H - 32, 30);
  c.fillStyle = "#8ba86a"; c.fill();
  c.strokeStyle = "#6f8a52"; c.lineWidth = 3; c.stroke();
  c.save(); c.clip();
  // grass pixel texture
  for (let y = 20; y < WORLD_H - 20; y += 16)
    for (let x = 20; x < WORLD_W - 20; x += 16) {
      const r = hash(x, y);
      if (r > 0.86) R(c, x, y, 6, 6, "#7d9a5c");
      else if (r < 0.1) R(c, x, y, 5, 5, "#97b477");
    }

  // cobble paths: plaza center -> each gather point
  c.lineCap = "round"; c.lineJoin = "round";
  for (const [name, z] of Object.entries(Z)) {
    if (name === "square") continue;
    c.strokeStyle = "#d9c49a"; c.lineWidth = 20;
    c.beginPath(); c.moveTo(CENTER.x, CENTER.y); c.lineTo(z.gx, z.gy); c.stroke();
    c.strokeStyle = "#c9b083"; c.lineWidth = 3;
    c.beginPath(); c.moveTo(CENTER.x, CENTER.y); c.lineTo(z.gx, z.gy); c.stroke();
  }

  // plaza
  c.beginPath();
  c.ellipse(PLAZA.x, PLAZA.y, PLAZA.rx, PLAZA.ry, 0, 0, Math.PI * 2);
  c.fillStyle = "#9fb86f"; c.fill();
  c.strokeStyle = "#7f9757"; c.lineWidth = 2; c.stroke();
  c.restore();

  // decorative bushes
  for (const [bx, by] of [[70, 90], [930, 100], [60, 560], [940, 560], [500, 40], [500, 600]])
    bush(c, bx, by);

  // buildings (sorted by y so lower ones overlap correctly)
  Object.keys(Z).sort((a, b) => Z[a].y - Z[b].y).forEach((z) => building(c, z, windows));

  // fountain basin (static; water shimmer added live)
  const f = FOUNTAIN;
  c.fillStyle = "#b9c2c8"; c.beginPath(); c.arc(f.x, f.y, 34, 0, Math.PI * 2); c.fill();
  c.strokeStyle = INK; c.lineWidth = 2.5; c.stroke();
  R(c, f.x - 3, f.y - 20, 6, 20, "#9aa6ad");

  return { canvas, windows };
}

// --- live per-frame layers ---
const SKY: Record<string, [string, string]> = {
  morning: ["#f6c99f", "#a9c8d8"], afternoon: ["#bfe0ec", "#d8ecc4"], evening: ["#3a2f56", "#6a5170"],
};

export function drawSky(c: CanvasRenderingContext2D, slot: string) {
  const [a, b] = SKY[slot] || SKY.afternoon;
  const g = c.createLinearGradient(0, 0, 0, WORLD_H);
  g.addColorStop(0, a); g.addColorStop(1, b);
  c.fillStyle = g; c.fillRect(0, 0, WORLD_W, WORLD_H);
}

export function drawFountain(c: CanvasRenderingContext2D, t: number) {
  const f = FOUNTAIN;
  c.fillStyle = "#6bb5d6"; c.beginPath(); c.arc(f.x, f.y, 24, 0, Math.PI * 2); c.fill();
  c.fillStyle = "#8fd3ec";
  c.beginPath(); c.arc(f.x, f.y - 22 - Math.sin(t / 300) * 2, 3.5, 0, Math.PI * 2); c.fill();
  const s = Math.sin(t / 260) * 3;
  R(c, f.x - 9, f.y - 16 - s * 0.3, 3, 5, "#bfe6f6");
  R(c, f.x + 7, f.y - 16 + s * 0.3, 3, 5, "#bfe6f6");
}

const FIREFLIES = [[300, 260], [680, 220], [460, 420], [780, 400], [220, 380]];

export function drawLighting(c: CanvasRenderingContext2D, slot: string, windows: Rect[], t: number) {
  if (slot !== "evening") return;
  // window glow
  c.save(); c.shadowColor = "#ffd27a"; c.shadowBlur = 8;
  for (const w of windows) R(c, w.x + 2, w.y + 2, w.w - 4, w.h - 4, "#ffd27a");
  c.restore();
  // dusk overlay
  c.fillStyle = "rgba(26,22,54,0.28)"; c.fillRect(16, 16, WORLD_W - 32, WORLD_H - 32);
  // fireflies
  FIREFLIES.forEach(([fx, fy], i) => {
    const p = ((t / 1000 + i * 0.9) % 5) / 5;
    const a = Math.sin(p * Math.PI);
    c.globalAlpha = a * 0.9;
    c.fillStyle = "#ffe89a";
    c.beginPath(); c.arc(fx + p * 14, fy - p * 34, 2.5, 0, Math.PI * 2); c.fill();
  });
  c.globalAlpha = 1;
}
