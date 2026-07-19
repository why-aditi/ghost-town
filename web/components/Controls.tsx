"use client";

const SLOTS = ["morning", "afternoon", "evening"];

export default function Controls({
  day, tick, ticking, phase, autoplay, onTick, onToggleAutoplay,
}: {
  day: number; tick: number; ticking: boolean; phase: string | null;
  autoplay: boolean; onTick: () => void; onToggleAutoplay: () => void;
}) {
  return (
    <header className="flex items-center gap-4 border-b border-zinc-800 px-5 py-3">
      <h1 className="text-lg font-bold tracking-tight text-zinc-100">
        👻 Ghost Town
      </h1>
      <span className="rounded-md bg-zinc-800 px-2.5 py-1 text-sm text-zinc-300">
        Day {day} · <span className="capitalize">{SLOTS[tick % 3]}</span>
      </span>

      <div className="ml-auto flex items-center gap-3">
        {ticking && phase && (
          <span className="animate-pulse text-sm text-emerald-400">{phase}</span>
        )}
        <button onClick={onTick} disabled={ticking}
          className="rounded-md bg-emerald-700 px-4 py-1.5 text-sm font-medium text-white
            hover:bg-emerald-600 disabled:cursor-not-allowed disabled:opacity-40">
          {ticking ? "Ticking…" : "Next Tick ▸"}
        </button>
        <button onClick={onToggleAutoplay} disabled={ticking && !autoplay}
          className={`rounded-md px-3 py-1.5 text-sm font-medium ${
            autoplay ? "bg-amber-600 text-white hover:bg-amber-500"
                     : "border border-zinc-700 text-zinc-300 hover:bg-zinc-800"}`}>
          {autoplay ? "◼ Stop" : "▶ Auto"}
        </button>
      </div>
    </header>
  );
}
