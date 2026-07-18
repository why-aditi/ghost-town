"""Pydantic v2 models: the typed payloads passed between tick phases.

World state lives in SQLite (see db.py); these are the in-flight proposals and
reports. LLMs will (Day 2+) emit AgentPlan/Dialogue as JSON validated here.
"""
from typing import Literal

from pydantic import BaseModel, Field

MemoryType = Literal["observation", "conversation", "reflection"]


class AgentPlan(BaseModel):
    """One agent's proposed move for a tick. LLM proposes; world.py disposes."""
    agent_id: str
    destination: str          # a zone id; validated against ZONES on apply
    action: str               # one of LEGAL_ACTIONS; flavor, not movement
    reason: str


class MemoryEntry(BaseModel):
    agent_id: str
    text: str
    type: MemoryType = "observation"
    importance: int = Field(default=1, ge=1, le=10)
    tick: int


class Dialogue(BaseModel):
    """A conversation between a co-located pair. Stub exchanges in Phase 1."""
    participants: list[str]   # exactly two agent ids
    zone: str
    exchanges: list[str] = []
    transfers: list[str] = []  # "information transferred" → both memory streams


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
    moves: dict[str, str] = {}          # agent_id -> destination applied
    rejected: list[str] = []            # agent_ids whose plan was rejected
    conversations: list[tuple[str, str]] = []
    narration: str = ""
    llm_calls: int = 0                  # always 0 in Phase 1 (stub minds)
