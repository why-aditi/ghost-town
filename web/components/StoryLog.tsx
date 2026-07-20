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
      <h2 className="font-display mb-3 text-sm font-bold uppercase tracking-[0.2em] text-amber-200/70">
        The Chronicle
      </h2>
      <div ref={ref} className="flex-1 space-y-4 overflow-y-auto pr-2">
        {entries.map((e, i) => (
          <div key={i}>
            <div className="font-hand text-base text-amber-300/70">
              Day {Math.floor(e.tick / 3)} · {SLOTS[e.tick % 3]}
            </div>
            <p className="font-serif text-[15px] leading-relaxed text-amber-50/85">{e.prose}</p>
          </div>
        ))}
        {entries.length === 0 && (
          <p className="font-serif italic text-amber-100/40">
            The town is quiet. Press <span className="text-amber-200">Next Tick</span> to begin the day.
          </p>
        )}
      </div>
    </div>
  );
}
