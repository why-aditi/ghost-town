"use client";
import { useEffect, useRef } from "react";
import { StoryEntry } from "@/lib/api";

const SLOTS = ["morning", "afternoon", "evening"];

export default function StoryLog({ entries }: { entries: StoryEntry[] }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    ref.current?.scrollTo({ top: ref.current.scrollHeight, behavior: "smooth" });
  }, [entries.length]);

  return (
    <div className="flex h-full flex-col">
      <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-500">
        The Chronicle
      </h2>
      <div ref={ref} className="flex-1 space-y-3 overflow-y-auto pr-2">
        {entries.map((e, i) => (
          <div key={i} className="border-l-2 border-zinc-800 pl-3">
            <div className="text-[11px] uppercase tracking-wide text-zinc-600">
              Day {Math.floor(e.tick / 3)} · {SLOTS[e.tick % 3]}
            </div>
            <p className="text-sm leading-relaxed text-zinc-300">{e.prose}</p>
          </div>
        ))}
        {entries.length === 0 && (
          <p className="text-sm text-zinc-600">
            No story yet. Press <span className="text-zinc-400">Next Tick</span> to begin.
          </p>
        )}
      </div>
    </div>
  );
}
