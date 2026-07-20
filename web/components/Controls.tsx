"use client";

const SLOTS = ["morning", "afternoon", "evening"];
const SUN: Record<string, string> = { morning: "🌅", afternoon: "☀️", evening: "🌙" };

export default function Controls({
  day, tick, ticking, phase, autoplay, onTick, onToggleAutoplay,
}: {
  day: number; tick: number; ticking: boolean; phase: string | null;
  autoplay: boolean; onTick: () => void; onToggleAutoplay: () => void;
}) {
  const slot = SLOTS[tick % 3];
  return (
    <header className="z-10 flex items-center gap-4 border-b border-amber-950/60 bg-[#1c1812] px-5 py-2.5">
      <h1 className="font-display text-xl font-bold tracking-wide text-amber-100">Ghost Town</h1>
      <span className="flex items-center gap-2 rounded-full border border-amber-900/50 bg-black/30 px-3 py-1 text-sm text-amber-100/90">
        <span className="text-base">{SUN[slot]}</span>
        <span className="font-display tracking-wide">Day {day}</span>
        <span className="capitalize text-amber-200/60">· {slot}</span>
      </span>

      <div className="ml-auto flex items-center gap-3">
        {ticking && phase && (
          <span className="font-hand animate-pulse text-lg text-amber-200">{phase}</span>
        )}
        <button onClick={onTick} disabled={ticking}
          className="rounded-lg border-b-2 border-amber-950 bg-amber-600 px-4 py-1.5 text-sm font-semibold
            text-amber-50 shadow hover:bg-amber-500 active:border-b-0 active:translate-y-px
            disabled:cursor-not-allowed disabled:opacity-40">
          {ticking ? "Ticking…" : "Next Tick ▸"}
        </button>
        <button onClick={onToggleAutoplay} disabled={ticking && !autoplay}
          className={`rounded-lg px-3 py-1.5 text-sm font-semibold ${
            autoplay ? "bg-rose-700 text-rose-50 hover:bg-rose-600"
                     : "border border-amber-900/60 text-amber-100/80 hover:bg-black/30"}`}>
          {autoplay ? "◼ Stop" : "▶ Auto"}
        </button>
      </div>
    </header>
  );
}
