"""Seed data: the 8 zones and 8 flammable agents (PRD §9, CLAUDE.md Seeding).

Data, not prose blobs. World state is built from this at first run.
"""

# The 8 zones. Constant, not a DB table — validate against this set.
# ponytail: zones never change at runtime; add a table only if that changes.
ZONES = ["homes", "cafe", "market", "farm", "well", "square", "bakery", "forge"]

# Legal actions a plan may carry. Movement is decided by `destination`;
# `action` is flavor recorded on the plan.
LEGAL_ACTIONS = ["work", "wander", "go_home", "idle"]

# Where each occupation works — nudges morning-to-work behavior in planning.
WORKPLACE = {
    "merchant": "market",
    "farmer": "farm",
    "baker": "bakery",
    "blacksmith": "forge",
    "cafe owner": "cafe",
    "well-keeper": "well",
    "gossip": "square",
}


# Each agent: id, name, occupation, home_zone, traits, daily_goals, secrets,
# sociability (0..1, drives conversation eagerness), initial_relationships.
# Relationships are directional: {other, sentiment (-1..1), summary}.
AGENTS = [
    {
        "id": "silas",
        "name": "Silas",
        "occupation": "merchant",
        "home_zone": "homes",
        "traits": ["shrewd", "evasive"],
        "daily_goals": ["sell goods at the market", "keep well away from Bram, who I owe money to"],
        "secrets": ["I cannot actually repay the money I owe Bram."],
        "sociability": 0.5,
        "initial_relationships": [
            {"other": "bram", "sentiment": -0.3,
             "summary": "I owe him money and he keeps reminding me."},
        ],
    },
    {
        "id": "bram",
        "name": "Bram",
        "occupation": "farmer",
        "home_zone": "homes",
        "traits": ["blunt", "patient"],
        "daily_goals": ["tend the farm", "track down Silas and demand the money he owes me"],
        "secrets": [],
        "sociability": 0.4,
        "initial_relationships": [
            {"other": "silas", "sentiment": -0.5,
             "summary": "He owes me money and dodges me every day."},
        ],
    },
    {
        "id": "elara",
        "name": "Elara",
        "occupation": "baker",
        "home_zone": "homes",
        "traits": ["warm", "competitive"],
        "daily_goals": ["bake fresh bread", "win Mira's heart before Rurik does"],
        "secrets": [],
        "sociability": 0.6,
        "initial_relationships": [
            {"other": "rurik", "sentiment": -0.4,
             "summary": "My rival for Mira's attention."},
            {"other": "mira", "sentiment": 0.6,
             "summary": "I hope to win her heart."},
        ],
    },
    {
        "id": "rurik",
        "name": "Rurik",
        "occupation": "blacksmith",
        "home_zone": "homes",
        "traits": ["gruff", "competitive"],
        "daily_goals": ["work the forge", "win Mira's heart before Elara does"],
        "secrets": [],
        "sociability": 0.5,
        "initial_relationships": [
            {"other": "elara", "sentiment": -0.4,
             "summary": "My rival for Mira's attention."},
            {"other": "mira", "sentiment": 0.6,
             "summary": "I hope to win her heart."},
        ],
    },
    {
        "id": "mira",
        "name": "Mira",
        "occupation": "cafe owner",
        "home_zone": "homes",
        "traits": ["charming", "observant"],
        "daily_goals": ["run the cafe", "keep the peace"],
        "secrets": [],
        "sociability": 0.7,
        "initial_relationships": [
            {"other": "elara", "sentiment": 0.1, "summary": "A sweet regular."},
            {"other": "rurik", "sentiment": 0.1, "summary": "A steady regular."},
        ],
    },
    {
        "id": "odette",
        "name": "Odette",
        "occupation": "well-keeper",
        "home_zone": "homes",
        "traits": ["quiet", "watchful"],
        "daily_goals": ["mind the well", "keep quiet about what I saw at the old mine"],
        "secrets": ["The old mine didn't collapse by accident — I saw who did it."],
        "sociability": 0.5,
        "initial_relationships": [],
    },
    {
        "id": "tilda",
        "name": "Tilda",
        "occupation": "gossip",
        "home_zone": "homes",
        "traits": ["talkative", "curious"],
        "daily_goals": ["hear the latest news", "share it widely"],
        "secrets": [],
        "sociability": 0.9,
        "initial_relationships": [
            {"other": "pip", "sentiment": 0.5, "summary": "My favourite source of news."},
        ],
    },
    {
        "id": "pip",
        "name": "Pip",
        "occupation": "gossip",
        "home_zone": "homes",
        "traits": ["talkative", "nosy"],
        "daily_goals": ["collect rumours", "trade them for more"],
        "secrets": [],
        "sociability": 0.9,
        "initial_relationships": [
            {"other": "tilda", "sentiment": 0.5, "summary": "Always knows something."},
        ],
    },
]
