"""Pydantic v2 models: the typed payloads passed between tick phases.

World state lives in SQLite (see db.py); these are the in-flight proposals and
reports. LLMs will (Day 2+) emit AgentPlan/Dialogue as JSON validated here.
"""
from typing import Literal

from pydantic import BaseModel, Field, RootModel

MemoryType = Literal["observation", "conversation", "reflection"]


class AgentPlan(BaseModel):
    """One agent's proposed move for a tick. LLM proposes; world.py disposes."""
    agent_id: str
    destination: str          # a zone id; validated against ZONES on apply
    action: str               # one of LEGAL_ACTIONS; flavor, not movement
    reason: str


class PlannedAction(BaseModel):
    """The LLM's decision for one agent (agent_id is the dict key, not here)."""
    destination: str
    action: str
    reason: str


class BatchPlan(RootModel[dict[str, PlannedAction]]):
    """Batched-mind output: JSON keyed by agent_id. One call plans everyone."""


class ImportanceScores(RootModel[dict[str, int]]):
    """Batched importance scoring: {memory_index (as str): score 1-10}."""


class ReflectionResult(RootModel[dict[str, list[str]]]):
    """Batched day-end reflection: {agent_id: [belief statements]}."""


class MemoryEntry(BaseModel):
    agent_id: str
    text: str
    type: MemoryType = "observation"
    importance: int = Field(default=1, ge=1, le=10)
    tick: int


class Dialogue(BaseModel):
    """A conversation between a co-located pair (post-validation)."""
    participants: list[str]   # exactly two agent ids
    zone: str
    exchanges: list[str] = []                    # "Name: text" lines, for the story log
    transfers: dict[str, list[str]] = {}         # learner_id -> facts learned (their POV)


# --- LLM dialogue output (Groq) ---
class DialogueTurn(BaseModel):
    speaker: str
    text: str


class RelationshipUpdate(BaseModel):
    sentiment_delta: float = 0.0
    summary: str


class DialogueResult(BaseModel):
    """One Groq call's full output for a pair."""
    exchanges: list[DialogueTurn] = []
    transfers: dict[str, list[str]] = {}         # learner_id -> facts learned (their POV)
    relationships: dict[str, RelationshipUpdate] = {}  # agent_id -> updated feeling


class WorldEvent(BaseModel):
    id: int | None = None
    tick: int
    zone: str
    description: str
    source: Literal["user", "system"] = "user"


class TickReport(BaseModel):
    tick: int
    time_slot: str
    day: int
    planned: dict[str, AgentPlan] = {}  # final decision per agent (post anti-bleed)
    moves: dict[str, str] = {}          # agent_id -> destination applied
    rejected: list[str] = []            # agent_ids whose plan was rejected/defaulted
    conversations: list[tuple[str, str]] = []
    transcripts: list[dict] = []        # {a,b,zone,gossip,lines,transfers} per dialogue
    gossip: list[str] = []              # "<learner> learned: <fact>" this tick
    reflections: list[str] = []         # "<agent>: <belief>" at day-end
    narration: str = ""
    quiet: bool = False                 # budget exceeded -> quiet tick, no planning call
    llm_calls: int = 0
