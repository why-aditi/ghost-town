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

# Conversations (Day 4)
MAX_CONVERSATIONS_PER_TICK = 3   # <= 3 dialogue calls/tick (plan+3+score = 5 <= 6)
DIALOGUE_TEMPERATURE = 0.7       # higher temp -> livelier dialogue
PAIR_SOC_W = 1.0                 # pairing: sociability weight
PAIR_REL_W = 0.8                 # pairing: |sentiment| weight (rivals talk too)
PAIR_ACQ_W = 0.3                 # pairing: already-acquainted bonus
PAIR_REPEAT_PENALTY = 2.5        # demote recently-paired BELOW any fresh pair
                                 # (> max base score 2.1), so a knower is forced to
                                 # talk to someone new -> gossip reaches new ears.
PAIR_COOLDOWN_TICKS = 3          # a pair is penalized for this many ticks after talking

# Reflections + narrator + events (Day 5)
REFLECT_TOP_N = 6                # day's memories fed to the reflection call, per agent
REFLECTION_IMPORTANCE = 8       # beliefs are stored as high-importance memories
USER_EVENT_IMPORTANCE = 7       # a user-injected event is notable, not mundane
NARRATOR_TEMPERATURE = 0.7
