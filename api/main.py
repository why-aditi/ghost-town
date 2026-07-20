"""FastAPI backend: one in-memory simulation the web UI drives.

Single long-lived World (ephemeral memory; persistent = P1). One tick at a time
(a `ticking` flag). POST /tick streams per-phase progress as SSE, then the
report; the clock advances after the tick, and /state reports the tick that
just ran (positions post-move) so the UI shows "what just happened".

    uvicorn api.main:app --reload
"""
import asyncio
import json
import random

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from sim import config
from sim.llm.client import LLMBudget
from sim.personas import ZONES
from sim.tick import run_tick_stream
from sim.world import World


class Sim:
    def __init__(self):
        self.world = World.new(":memory:")
        self.budget = LLMBudget(config.BUDGET_PER_DAY)
        self.rng = random.Random(42)
        self.last_report = None
        self.ticking = False


SIM = Sim()

app = FastAPI(title="Ghost Town")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])


@app.get("/state")
def get_state():
    w = SIM.world.state()
    r = SIM.last_report
    pos = {a["id"]: a["position"] for a in SIM.world.agents()}
    # who learned a secret this tick (so the UI can ripple those conversations)
    learners = {g.split(" learned:")[0] for g in (r.gossip if r else [])}
    convos = [{"a": a, "b": b, "zone": pos.get(a, ""),
               "gossip": a in learners or b in learners}
              for a, b in (r.conversations if r else [])]
    return {
        "tick": r.tick if r else w["tick"],
        "day": r.day if r else w["day"],
        "time_slot": r.time_slot if r else w["time_slot"],
        "zones": ZONES,
        "agents": [{"id": a["id"], "name": a["name"], "occupation": a["occupation"],
                    "position": a["position"]} for a in SIM.world.agents()],
        "conversations": convos,
        "gossip": r.gossip if r else [],
        "ticking": SIM.ticking,
    }


@app.get("/agents/{agent_id}")
def get_agent(agent_id: str):
    a = SIM.world.agent(agent_id)
    if a is None:
        raise HTTPException(404, "no such agent")
    plan = SIM.last_report.planned.get(agent_id) if SIM.last_report else None
    mems = sorted(SIM.world.memory.all(agent_id),
                  key=lambda m: m["importance"], reverse=True)[:8]
    return {
        "id": a["id"], "name": a["name"], "occupation": a["occupation"],
        "position": a["position"], "traits": a["traits"], "goals": a["daily_goals"],
        "plan": plan.model_dump() if plan else None,
        "memories": [{"type": m["type"], "importance": m["importance"],
                      "text": m["text"], "tick": m["tick"]} for m in mems],
        "relationships": SIM.world.relationships(agent_id),
    }


class EventIn(BaseModel):
    zone: str
    description: str


@app.post("/events")
def inject_event(ev: EventIn):
    if ev.zone not in SIM.world.zones:
        raise HTTPException(400, f"unknown zone; valid: {', '.join(ZONES)}")
    SIM.world.inject_event(ev.zone, ev.description, source="user")
    return {"ok": True, "zone": ev.zone}


@app.get("/story")
def get_story():
    return SIM.world.db.get_story()


@app.post("/tick")
async def post_tick():
    if SIM.ticking:
        raise HTTPException(409, "a tick is already running")
    SIM.ticking = True

    async def stream():
        q: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def worker():
            # Runs the whole tick off the event loop. Advances the clock + clears
            # `ticking` HERE (not in the stream) so a client disconnect can't
            # advance mid-tick — the tick always completes first.
            try:
                for phase, data in run_tick_stream(SIM.world, SIM.rng, SIM.budget):
                    if phase == "report":
                        SIM.last_report = data
                        payload = data.model_dump(mode="json")
                    else:
                        payload = data
                    loop.call_soon_threadsafe(q.put_nowait, (phase, payload))
            except Exception as e:  # noqa: BLE001 - report to the client, don't hang
                loop.call_soon_threadsafe(q.put_nowait, ("error", {"detail": str(e)[:200]}))
            finally:
                SIM.world.advance_time()   # advance AFTER the tick (like cli.py)
                SIM.ticking = False
                loop.call_soon_threadsafe(q.put_nowait, None)

        loop.run_in_executor(None, worker)
        while True:
            item = await q.get()
            if item is None:
                break
            phase, payload = item
            yield {"event": phase, "data": json.dumps(payload)}

    return EventSourceResponse(stream())
