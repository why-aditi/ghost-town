"""Authoritative world state, mutated ONLY through validated functions.

LLM-PROPOSES / CODE-DISPOSES (CLAUDE.md): plans are proposals; apply_plan
validates and either applies or rejects. Nothing else touches positions.
"""
from sim import config
from sim.db import DB
from sim.models import AgentPlan
from sim.personas import AGENTS, LEGAL_ACTIONS, ZONES
from sim.phases.memory import MemoryStore

_TIME_SLOTS = ["morning", "afternoon", "evening"]


class World:
    def __init__(self, db: DB, memory: MemoryStore):
        self.db = db
        self.memory = memory
        self.zones = set(ZONES)

    @classmethod
    def new(cls, db_path: str = ":memory:", memory_path: str | None = None,
            embedding_function=None, agents: list[dict] = AGENTS) -> "World":
        w = cls(DB(db_path), MemoryStore(memory_path, embedding_function))
        if not w.db.is_seeded():
            w._seed(agents)
        return w

    def _seed(self, agents: list[dict]) -> None:
        self.db.set_world(tick=0, time_slot=_TIME_SLOTS[0], day=0)
        for a in agents:
            self.db.insert_agent(a)
        for a in agents:
            for rel in a["initial_relationships"]:
                self.db.insert_relationship(a["id"], rel["other"], rel["sentiment"],
                                            rel["summary"], tick=0)
        # Seed memories: an agent starts knowing their own secrets + relationships.
        for a in agents:
            for secret in a["secrets"]:
                self.memory.add(a["id"], secret, "observation", 0, config.SEED_SECRET_IMPORTANCE)
            for rel in a["initial_relationships"]:
                self.memory.add(a["id"], rel["summary"], "observation", 0, config.SEED_REL_IMPORTANCE)

    # --- reads ---
    def state(self) -> dict:
        return self.db.get_world()

    def agents(self) -> list[dict]:
        return self.db.get_agents()

    def agent(self, agent_id: str) -> dict | None:
        return self.db.get_agent(agent_id)

    def positions(self) -> dict[str, str]:
        return {a["id"]: a["position"] for a in self.db.get_agents()}

    def relationships(self, agent_id: str) -> list[dict]:
        return self.db.get_relationships(agent_id)

    # --- validated mutations ---
    def move_agent(self, agent_id: str, zone: str) -> None:
        """Direct move. Raises on illegal input (programmer error)."""
        if self.db.get_agent(agent_id) is None:
            raise ValueError(f"unknown agent: {agent_id}")
        if zone not in self.zones:
            raise ValueError(f"unknown zone: {zone}")
        self.db.set_position(agent_id, zone)

    def apply_plan(self, plan: AgentPlan) -> tuple[bool, str | None]:
        """Validate a proposed plan; apply if legal. Returns (applied, reason).

        Rejected plans are NOT applied — the caller defaults the agent to a
        safe action. This is the seam the Day-2 anti-bleed validator plugs into.
        """
        if self.db.get_agent(plan.agent_id) is None:
            return False, f"unknown agent: {plan.agent_id}"
        if plan.destination not in self.zones:
            return False, f"unknown zone: {plan.destination}"
        if plan.action not in LEGAL_ACTIONS:
            return False, f"illegal action: {plan.action}"
        self.db.set_position(plan.agent_id, plan.destination)
        return True, None

    def advance_time(self) -> dict:
        w = self.db.get_world()
        tick = w["tick"] + 1
        self.db.set_world(tick, _TIME_SLOTS[tick % 3], tick // 3)
        return self.db.get_world()

    def inject_event(self, zone: str, description: str, source: str = "user") -> int:
        if zone not in self.zones:
            raise ValueError(f"unknown zone: {zone}")
        return self.db.add_event(self.db.get_world()["tick"], zone, description, source)

    def events_at(self, zone: str) -> list[dict]:
        return self.db.events_at(zone)

    def add_story(self, tick: int, prose: str) -> None:
        self.db.add_story(tick, prose)
