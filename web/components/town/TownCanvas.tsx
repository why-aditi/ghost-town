"use client";
import { useEffect, useRef } from "react";
import { State } from "@/lib/api";
import { WORLD_W, WORLD_H } from "./layout";
import { bakeScene, drawSky, drawSunlight, drawClouds, drawFoliage, drawSmoke, drawFountain, drawLighting, Rect } from "./scene";
import { drawCharacter, drawCritter, CHAR_H } from "./sprites";
import { World, createWorld, step, syncFromState, reducedMotion } from "./worldModel";
import { emoteFor } from "./emotes";
import { audio } from "./audio";

type Convo = State["conversations"][number];
type Props = {
  state: State; selected: string | null;
  onSelect: (id: string) => void; onConversation: (c: Convo) => void;
  follow?: boolean; onFollowEnd?: () => void; resetNonce?: number;
};

type SpriteHit = { x: number; y: number; id: string };
type BubbleHit = { x: number; y: number; convo: Convo };

function drawAgents(ctx: CanvasRenderingContext2D, w: World, now: number,
                   selected: string | null, font: string, out: SpriteHit[]) {
  const list = Array.from(w.agents.values()).sort((a, b) => a.y - b.y);
  ctx.textAlign = "center"; ctx.textBaseline = "alphabetic";
  for (const ag of list) {
    const bob = ag.walking || reducedMotion ? 0
      : Math.sin((now / 1000 + ag.bobPhase) * (Math.PI * 2 / 2.4)) * -2.5;
    const y = ag.y + bob;
    ctx.fillStyle = "rgba(0,0,0,0.22)";
    ctx.beginPath(); ctx.ellipse(ag.x, ag.y + 2, 11, 3.5, 0, 0, Math.PI * 2); ctx.fill();
    if (ag.id === selected) {
      ctx.strokeStyle = "#ffd27a"; ctx.lineWidth = 2.5;
      ctx.beginPath(); ctx.ellipse(ag.x, y - 16, 19, 24, 0, 0, Math.PI * 2); ctx.stroke();
    }
    ctx.save(); ctx.translate(ag.x, y); if (ag.dir === "left") ctx.scale(-1, 1);
    const frame = ag.walking ? (Math.floor(ag.walkPhase * 7) % 2) + 1 : 0;
    drawCharacter(ctx, ag.tunic, ag.occupation, frame, ag.dir);
    ctx.restore();
    ctx.font = `700 13px ${font}`;
    ctx.lineWidth = 3; ctx.strokeStyle = "#17140f"; ctx.strokeText(ag.name, ag.x, ag.y + 17);
    ctx.fillStyle = "#f2e8d4"; ctx.fillText(ag.name, ag.x, ag.y + 17);
    const em = emoteFor(ag, now);
    if (em) {
      ctx.globalAlpha = Math.min(1, (1 - em.phase) * 2.4);   // hold, then fade
      ctx.font = "18px sans-serif";
      ctx.fillText(em.emoji, ag.x, y - CHAR_H - 4 - em.phase * 16);
      ctx.globalAlpha = 1;
    }
    out.push({ x: ag.x, y: ag.y, id: ag.id });
  }
}

function drawCritters(ctx: CanvasRenderingContext2D, w: World, now: number) {
  for (const cr of w.critters) {
    const frame = Math.floor((now / 1000 + cr.phase) * 6) % 2;
    if (cr.kind !== "bird") {   // ground critters cast a small shadow
      ctx.fillStyle = "rgba(0,0,0,0.18)";
      ctx.beginPath(); ctx.ellipse(cr.x, cr.y + 1, 7, 2.5, 0, 0, Math.PI * 2); ctx.fill();
    }
    ctx.save(); ctx.translate(cr.x, cr.y); if (cr.facing < 0) ctx.scale(-1, 1);
    drawCritter(ctx, cr.kind, frame); ctx.restore();
  }
}

function drawBubbles(ctx: CanvasRenderingContext2D, w: World, now: number, out: BubbleHit[]) {
  for (const c of w.conversations) {
    const a = w.agents.get(c.a), b = w.agents.get(c.b);
    if (!a || !b || a.walking || b.walking || a.zone !== c.zone || b.zone !== c.zone) continue;
    const mx = (a.x + b.x) / 2, my = Math.min(a.y, b.y) - 48;
    if (c.gossip) {
      const p = (now % 1600) / 1600;
      ctx.globalAlpha = (1 - p) * 0.9; ctx.strokeStyle = "#ffcf70"; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(mx, my + 16, 6 + p * 38, 0, Math.PI * 2); ctx.stroke();
      ctx.globalAlpha = 1;
      ctx.strokeStyle = "#ffd27a"; ctx.lineWidth = 2.5;
      ctx.setLineDash([3, 5]); ctx.lineDashOffset = -(now / 60) % 8;
      ctx.beginPath(); ctx.moveTo(a.x, a.y - 20); ctx.quadraticCurveTo(mx, my - 4, b.x, b.y - 20); ctx.stroke();
      ctx.setLineDash([]);
    }
    ctx.fillStyle = c.gossip ? "#fff3d6" : "#fbf6ea"; ctx.strokeStyle = "#4a3f30"; ctx.lineWidth = 1.5;
    ctx.beginPath(); (ctx as any).roundRect(mx - 18, my - 15, 36, 26, 10); ctx.fill(); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(mx - 4, my + 10); ctx.lineTo(mx + 4, my + 10); ctx.lineTo(mx, my + 18); ctx.closePath();
    ctx.fill(); ctx.stroke();
    ctx.font = "16px sans-serif"; ctx.textAlign = "center";
    ctx.fillText(c.gossip ? "🤫" : "💬", mx, my + 3);
    out.push({ x: mx, y: my, convo: c });
  }
}

export default function TownCanvas({ state, selected, onSelect, onConversation, follow, onFollowEnd, resetNonce }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wrapRef = useRef<HTMLDivElement>(null);
  const worldRef = useRef<World>();
  const sceneRef = useRef<{ canvas: HTMLCanvasElement; windows: Rect[] }>();
  const fitRef = useRef({ scale: 1, dpr: 1 });
  const camRef = useRef({ zoom: 1, panX: 0, panY: 0, dragging: false, lastX: 0, lastY: 0, moved: false });
  const fontRef = useRef("cursive");
  const spriteHits = useRef<SpriteHit[]>([]);
  const bubbleHits = useRef<BubbleHit[]>([]);
  const cbRef = useRef({ selected, onSelect, onConversation, follow, onFollowEnd });
  cbRef.current = { selected, onSelect, onConversation, follow, onFollowEnd };

  if (!worldRef.current) worldRef.current = createWorld();

  // HUD "reset view" bumps resetNonce → recenter at 1×.
  useEffect(() => { const c = camRef.current; c.zoom = 1; c.panX = 0; c.panY = 0; }, [resetNonce]);

  useEffect(() => {
    sceneRef.current = bakeScene();
    document.fonts?.ready.then(() => {
      fontRef.current = getComputedStyle(document.documentElement)
        .getPropertyValue("--font-hand").trim() || "cursive";
    });
  }, []);

  const lastGossip = useRef(-1);
  useEffect(() => {
    if (!worldRef.current) return;
    syncFromState(worldRef.current, state);
    if (state.conversations?.some((c) => c.gossip) && state.tick !== lastGossip.current) {
      lastGossip.current = state.tick; audio.chime();
    }
  }, [state]);

  useEffect(() => {
    const fit = () => {
      const cv = canvasRef.current, wrap = wrapRef.current;
      if (!cv || !wrap) return;
      const scale = Math.min(wrap.clientWidth / WORLD_W, wrap.clientHeight / WORLD_H);
      const dispW = WORLD_W * scale, dispH = WORLD_H * scale;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      cv.width = Math.round(dispW * dpr); cv.height = Math.round(dispH * dpr);
      cv.style.width = `${dispW}px`; cv.style.height = `${dispH}px`;
      fitRef.current = { scale, dpr };
    };
    fit();
    const ro = new ResizeObserver(fit);
    if (wrapRef.current) ro.observe(wrapRef.current);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    let raf = 0, last = performance.now(), running = true;
    const loop = (now: number) => {
      if (!running) return;
      const dt = Math.min(now - last, 50); last = now;
      const cv = canvasRef.current, w = worldRef.current, scene = sceneRef.current;
      if (cv && w) {
        const ctx = cv.getContext("2d")!;
        const { scale, dpr } = fitRef.current;
        const cam = camRef.current;
        const dispW = WORLD_W * scale, dispH = WORLD_H * scale;
        if (cbRef.current.follow && cbRef.current.selected) {
          const a = w.agents.get(cbRef.current.selected);
          if (a) { cam.panX = dispW / 2 - a.x * scale * cam.zoom; cam.panY = dispH / 2 - a.y * scale * cam.zoom; }
        }
        cam.panX = Math.min(0, Math.max(dispW * (1 - cam.zoom), cam.panX));
        cam.panY = Math.min(0, Math.max(dispH * (1 - cam.zoom), cam.panY));
        const k = scale * cam.zoom * dpr;
        ctx.setTransform(k, 0, 0, k, cam.panX * dpr, cam.panY * dpr);
        ctx.imageSmoothingEnabled = false;
        step(w, dt);
        drawSky(ctx, w.slot);
        if (scene) ctx.drawImage(scene.canvas, 0, 0);
        const at = reducedMotion ? 0 : now;   // freeze ambient motion for reduced-motion
        drawSunlight(ctx, w.slot, at);
        if (!reducedMotion) { drawClouds(ctx, w.slot, now); drawSmoke(ctx, now); }
        drawFoliage(ctx, at);
        drawFountain(ctx, at);
        drawCritters(ctx, w, now);
        spriteHits.current = []; bubbleHits.current = [];
        drawAgents(ctx, w, now, cbRef.current.selected, fontRef.current, spriteHits.current);
        drawBubbles(ctx, w, now, bubbleHits.current);
        if (scene) drawLighting(ctx, w.slot, scene.windows, now);
        let walking = false; w.agents.forEach((a) => { if (a.walking) walking = true; });
        if (walking) audio.step(now);
      }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    const vis = () => {
      if (document.hidden) { running = false; cancelAnimationFrame(raf); }
      else if (!running) { running = true; last = performance.now(); raf = requestAnimationFrame(loop); }
    };
    document.addEventListener("visibilitychange", vis);
    return () => { running = false; cancelAnimationFrame(raf); document.removeEventListener("visibilitychange", vis); };
  }, []);

  // display-px → world, inverting the camera zoom+pan (must track the loop's transform)
  const toWorld = (e: React.MouseEvent | { clientX: number; clientY: number }) => {
    const cv = canvasRef.current!; const r = cv.getBoundingClientRect();
    const { scale } = fitRef.current; const cam = camRef.current;
    return {
      x: ((e.clientX - r.left) - cam.panX) / (scale * cam.zoom),
      y: ((e.clientY - r.top) - cam.panY) / (scale * cam.zoom),
    };
  };
  const hitTest = (x: number, y: number) =>
    bubbleHits.current.some((b) => Math.hypot(x - b.x, y - b.y) < 20)
    || spriteHits.current.some((s) => Math.abs(x - s.x) < 16 && y < s.y + 4 && y > s.y - CHAR_H);

  const onClick = (e: React.MouseEvent) => {
    if (camRef.current.moved) return;              // a drag, not a click
    const { x, y } = toWorld(e);
    for (const b of bubbleHits.current) if (Math.hypot(x - b.x, y - b.y) < 20)
      return cbRef.current.onConversation(b.convo);
    for (const s of [...spriteHits.current].sort((a, b) => b.y - a.y))
      if (Math.abs(x - s.x) < 16 && y < s.y + 4 && y > s.y - CHAR_H) {
        audio.click(); return cbRef.current.onSelect(s.id);
      }
  };
  const onDown = (e: React.MouseEvent) => {
    const c = camRef.current; c.dragging = true; c.moved = false; c.lastX = e.clientX; c.lastY = e.clientY;
  };
  const onUp = () => { camRef.current.dragging = false; };
  const onMove = (e: React.MouseEvent) => {
    const c = camRef.current;
    if (c.dragging) {
      const dx = e.clientX - c.lastX, dy = e.clientY - c.lastY;
      if (Math.abs(dx) + Math.abs(dy) > 3) c.moved = true;
      c.panX += dx; c.panY += dy; c.lastX = e.clientX; c.lastY = e.clientY;
      if (c.moved && cbRef.current.follow) cbRef.current.onFollowEnd?.();
      canvasRef.current!.style.cursor = "grabbing";
      return;
    }
    const { x, y } = toWorld(e);
    canvasRef.current!.style.cursor = hitTest(x, y) ? "pointer" : (c.zoom > 1 ? "grab" : "default");
  };
  const onDouble = () => { const c = camRef.current; c.zoom = 1; c.panX = 0; c.panY = 0; cbRef.current.onFollowEnd?.(); };

  // wheel zoom about the cursor (native listener so preventDefault isn't passive-blocked)
  useEffect(() => {
    const cv = canvasRef.current; if (!cv) return;
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      const r = cv.getBoundingClientRect(); const { scale } = fitRef.current; const c = camRef.current;
      const dx = e.clientX - r.left, dy = e.clientY - r.top;
      const wx = (dx - c.panX) / (scale * c.zoom), wy = (dy - c.panY) / (scale * c.zoom);
      c.zoom = Math.min(3, Math.max(1, c.zoom * (e.deltaY < 0 ? 1.12 : 0.89)));
      c.panX = dx - wx * scale * c.zoom; c.panY = dy - wy * scale * c.zoom;
      if (cbRef.current.follow) cbRef.current.onFollowEnd?.();
    };
    cv.addEventListener("wheel", onWheel, { passive: false });
    return () => cv.removeEventListener("wheel", onWheel);
  }, []);

  return (
    <div ref={wrapRef} className="grid h-full w-full place-items-center">
      <canvas ref={canvasRef} onClick={onClick} onMouseMove={onMove} onMouseDown={onDown}
        onMouseUp={onUp} onMouseLeave={onUp} onDoubleClick={onDouble}
        style={{ borderRadius: 16, boxShadow: "0 8px 30px rgba(0,0,0,.45)", imageRendering: "pixelated" }} />
    </div>
  );
}
