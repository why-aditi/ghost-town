"""SQLite world state + story log (PRD §8). Thin storage layer.

Low-level row ops only — validation and domain rules live in world.py.
Memories live here in Phase 1 as a stub stream; they migrate to ChromaDB
collections on Day 3 (that's when retrieval scoring lands).
"""
import json
import sqlite3

_SCHEMA = """
CREATE TABLE IF NOT EXISTS world (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    tick INTEGER NOT NULL,
    time_slot TEXT NOT NULL,
    day INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    occupation TEXT NOT NULL,
    home_zone TEXT NOT NULL,
    position TEXT NOT NULL,
    traits TEXT NOT NULL,          -- json list
    daily_goals TEXT NOT NULL,     -- json list
    secrets TEXT NOT NULL,         -- json list
    sociability REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS relationships (
    agent_id TEXT NOT NULL,
    other_id TEXT NOT NULL,
    sentiment REAL NOT NULL,
    summary TEXT NOT NULL,
    updated_tick INTEGER NOT NULL,
    PRIMARY KEY (agent_id, other_id)
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tick_injected INTEGER NOT NULL,
    zone TEXT NOT NULL,
    description TEXT NOT NULL,
    source TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS story_log (
    tick INTEGER NOT NULL,
    prose TEXT NOT NULL
);
"""
# Memories live in ChromaDB (per-agent collections), not sqlite — see phases/memory.py.


class DB:
    def __init__(self, path: str = ":memory:"):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(_SCHEMA)
        self.conn.commit()

    # --- world clock ---
    def get_world(self) -> dict:
        row = self.conn.execute("SELECT tick, time_slot, day FROM world WHERE id = 1").fetchone()
        return dict(row) if row else None

    def set_world(self, tick: int, time_slot: str, day: int) -> None:
        self.conn.execute(
            "INSERT INTO world (id, tick, time_slot, day) VALUES (1, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET tick=?, time_slot=?, day=?",
            (tick, time_slot, day, tick, time_slot, day),
        )
        self.conn.commit()

    # --- agents ---
    def insert_agent(self, a: dict) -> None:
        self.conn.execute(
            "INSERT INTO agents (id, name, occupation, home_zone, position, "
            "traits, daily_goals, secrets, sociability) VALUES (?,?,?,?,?,?,?,?,?)",
            (a["id"], a["name"], a["occupation"], a["home_zone"], a["home_zone"],
             json.dumps(a["traits"]), json.dumps(a["daily_goals"]),
             json.dumps(a["secrets"]), a["sociability"]),
        )
        self.conn.commit()

    def get_agents(self) -> list[dict]:
        rows = self.conn.execute("SELECT * FROM agents ORDER BY id").fetchall()
        return [self._agent_row(r) for r in rows]

    def get_agent(self, agent_id: str) -> dict | None:
        row = self.conn.execute("SELECT * FROM agents WHERE id = ?", (agent_id,)).fetchone()
        return self._agent_row(row) if row else None

    def set_position(self, agent_id: str, zone: str) -> None:
        self.conn.execute("UPDATE agents SET position = ? WHERE id = ?", (zone, agent_id))
        self.conn.commit()

    @staticmethod
    def _agent_row(r: sqlite3.Row) -> dict:
        d = dict(r)
        for k in ("traits", "daily_goals", "secrets"):
            d[k] = json.loads(d[k])
        return d

    # --- relationships ---
    def insert_relationship(self, agent_id: str, other_id: str, sentiment: float,
                            summary: str, tick: int) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO relationships "
            "(agent_id, other_id, sentiment, summary, updated_tick) VALUES (?,?,?,?,?)",
            (agent_id, other_id, sentiment, summary, tick),
        )
        self.conn.commit()

    def get_relationships(self, agent_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT other_id, sentiment, summary, updated_tick FROM relationships "
            "WHERE agent_id = ? ORDER BY other_id", (agent_id,)).fetchall()
        return [dict(r) for r in rows]

    def get_relationship(self, agent_id: str, other_id: str) -> dict | None:
        row = self.conn.execute(
            "SELECT sentiment, summary, updated_tick FROM relationships "
            "WHERE agent_id = ? AND other_id = ?", (agent_id, other_id)).fetchone()
        return dict(row) if row else None

    # --- events ---
    def add_event(self, tick: int, zone: str, description: str, source: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO events (tick_injected, zone, description, source) VALUES (?,?,?,?)",
            (tick, zone, description, source))
        self.conn.commit()
        return cur.lastrowid

    def events_at(self, zone: str) -> list[dict]:
        rows = self.conn.execute("SELECT * FROM events WHERE zone = ? ORDER BY id", (zone,)).fetchall()
        return [dict(r) for r in rows]

    # --- story log ---
    def add_story(self, tick: int, prose: str) -> None:
        self.conn.execute("INSERT INTO story_log (tick, prose) VALUES (?, ?)", (tick, prose))
        self.conn.commit()

    def get_story(self) -> list[dict]:
        rows = self.conn.execute("SELECT tick, prose FROM story_log ORDER BY rowid").fetchall()
        return [dict(r) for r in rows]

    def is_seeded(self) -> bool:
        return self.conn.execute("SELECT COUNT(*) FROM agents").fetchone()[0] > 0
