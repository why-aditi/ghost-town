// Procedural blocky characters. Drawn right-facing with feet at the local
// origin (0,0), up = -y. Caller translates to the feet position, applies the
// idle bob, and mirrors (scale(-1,1)) for left-facing. imageSmoothingEnabled
// is off, so integer rects read as chunky pixel-art.
const SKIN = "#eab892", HAIR = "#5a3d28", INK = "#4a3f30", SHOE = "#4a3527";

function darken(hex: string, k = 0.72): string {
  const n = parseInt(hex.slice(1), 16);
  const r = Math.round(((n >> 16) & 255) * k);
  const g = Math.round(((n >> 8) & 255) * k);
  const b = Math.round((n & 255) * k);
  return `rgb(${r},${g},${b})`;
}
const R = (c: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, col: string) => {
  c.fillStyle = col; c.fillRect(x, y, w, h);
};

// frame: 0 idle, 1 step-A, 2 step-B
export function drawCharacter(c: CanvasRenderingContext2D, tunic: string,
                             occupation: string, frame: number) {
  const pants = darken(tunic, 0.55);

  // legs (walk cycle raises one foot)
  const la = frame === 1 ? 10 : frame === 2 ? 7 : 10;
  const ra = frame === 1 ? 7 : frame === 2 ? 10 : 10;
  R(c, -6, -la, 5, la, pants);
  R(c, 1, -ra, 5, ra, pants);
  R(c, -6, -2, 5, 2, SHOE);
  R(c, 1, -2, 5, 2, SHOE);

  // torso + sleeves + hands
  R(c, -7, -22, 14, 12, tunic);
  R(c, -7, -13, 14, 2, pants);                 // belt
  R(c, -9, -21, 3, 9, tunic);
  R(c, 6, -21, 3, 9, tunic);
  R(c, -9, -13, 3, 3, SKIN);
  R(c, 6, -13, 3, 3, SKIN);

  // head
  R(c, -6, -33, 12, 11, SKIN);
  R(c, -3, -28, 2, 2, INK);
  R(c, 1, -28, 2, 2, INK);
  // default hair
  R(c, -6, -34, 12, 3, HAIR);
  R(c, -6, -31, 2, 5, HAIR);
  R(c, 4, -31, 2, 5, HAIR);

  // occupation-identifying hat / tool
  switch (occupation) {
    case "baker": // white toque + apron
      R(c, -6, -37, 12, 4, "#f5f0e6");
      R(c, -5, -40, 10, 3, "#f5f0e6");
      R(c, -5, -19, 10, 9, "#efe7d6");
      break;
    case "farmer": // straw hat + wheat
      R(c, -10, -33, 20, 2, "#d9b25a");
      R(c, -5, -37, 10, 4, "#c99a3e");
      R(c, 8, -22, 2, 8, "#e3c766");
      R(c, 7, -24, 4, 3, "#e3c766");
      break;
    case "blacksmith": // bandana + leather apron + hammer
      R(c, -6, -34, 12, 3, "#3a3a3a");
      R(c, -6, -20, 12, 10, "#6b4a2f");
      R(c, 8, -18, 2, 9, "#6b4a2f");
      R(c, 7, -19, 5, 3, "#9aa0a6");
      break;
    case "cafe owner": // apron + tray + bun
      R(c, -5, -19, 10, 9, "#efe7d6");
      R(c, 6, -14, 8, 2, "#c9a15a");
      R(c, -2, -36, 4, 3, HAIR);
      break;
    case "merchant": // feathered cap + coin pouch
      R(c, -6, -36, 12, 3, darken(tunic, 0.5));
      R(c, -6, -33, 12, 2, darken(tunic, 0.5));
      R(c, 5, -41, 2, 6, "#4fae6d");
      R(c, -10, -13, 3, 4, "#caa24a");
      break;
    case "well-keeper": // headscarf + bucket
      R(c, -6, -35, 12, 5, "#6b8fb0");
      R(c, -6, -30, 2, 3, "#6b8fb0");
      R(c, 4, -30, 2, 3, "#6b8fb0");
      R(c, 8, -13, 5, 5, "#9aa6ad");
      R(c, 8, -13, 5, 1, "#c2ccd2");
      break;
    case "gossip": // shawl + tall hair
      R(c, -8, -20, 16, 3, darken(tunic, 0.8));
      R(c, -6, -36, 12, 3, HAIR);
      R(c, -7, -33, 2, 8, HAIR);
      R(c, 5, -33, 2, 8, HAIR);
      break;
  }
}

export const CHAR_H = 42; // approx sprite height above feet, for bbox/label
