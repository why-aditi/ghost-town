"""Tunable constants (CLAUDE.md: retrieval weights live in config)."""

# Memory retrieval score = ALPHA*relevance + BETA*recency + GAMMA*importance
ALPHA = 1.0
BETA = 0.8
GAMMA = 0.6
RECENCY_DECAY = 0.98        # recency = RECENCY_DECAY ** (now_tick - memory_tick)

TOP_K_PLAN = 3              # memories retrieved per agent for planning
TOP_K_CONV = 5             # ... for conversations (Day 4)
FETCH_N = 20               # chroma candidates pulled before re-ranking

DEFAULT_IMPORTANCE = 3     # fallback when LLM scoring is skipped/fails
SEED_SECRET_IMPORTANCE = 8
SEED_REL_IMPORTANCE = 5

BUDGET_PER_DAY = 60        # LLM calls per simulated day before quiet-tick
