# Ghost Town

A simulated town of 8 LLM agents with jobs, memories, relationships, and goals.
Tick-based simulation; gossip propagates mechanically through memory; user
injects events and watches emergence. Full spec in docs/PRD.md — READ IT FIRST.
PRD is source of truth; if my instructions conflict with it, ask me.

## Non-negotiable architecture decisions (PRD §6)
- LLM-PROPOSES / CODE-DISPOSES: world state is authoritative in the DB and
  mutated ONLY by validated Python. LLMs return proposals; validation applies
  or rejects them. No exceptions.
- BATCHED-MIND PLANNING: ONE LLM call plans ALL agents per tick (strict
  per-agent prompt sections, JSON output keyed by agent id). Never one call
  per agent for planning. Budget: ≤ 6 LLM calls per tick, ≤ 60 per simulated
  day, enforced by a counter that degrades to "quiet tick" (agents continue
  current activity, no conversations) when exceeded.
- Conversations ARE per-pair calls (dialogue quality needs it): one call
  generates the whole 2–4 exchange dialogue.
- INFORMATION = MEMORY: an agent knows a fact only if it's in their memory
  stream. Gossip works by writing "information transferred" items from
  conversations into both participants' streams. Never leak world state or
  other agents' plans into a prompt beyond what that agent could know.
- Anti-bleed validation: after batched planning, reject any action whose
  reason references information absent from that agent's memories; rejected
  agents default to a safe action (continue/go home).
- Memory retrieval score = α·relevance + β·recency + γ·importance
  (α=1.0, β=0.8, γ=0.6 to start; constants in config). Top-3 for planning,
  top-5 for conversations.
- Tick phases in strict order: plan → move/act → conversations → memory
  writes → narrator. Implemented as a LangGraph graph per tick.

## Stack & pinned versions
- Python 3.11.9 (`py -3.11`; the bare `python` on this box is 3.14 — don't use it)
- Installed (exact, see requirements.txt for full lock):
  langgraph==1.2.9, langchain-core==1.4.9, chromadb==1.5.9,
  pydantic==2.13.4, pytest==9.1.1, groq==1.5.0. Python pinned via .python-version
  (3.11.9) so Render/CI don't default to 3.14.
- MISTRAL via raw HTTP (httpx), NOT the mistralai SDK. sim/llm/client._mistral
  POSTs the OpenAI-compatible https://api.mistral.ai/v1/chat/completions. Reason:
  mistralai 2.7.0 pins opentelemetry-semantic-conventions<0.61, which conflicts
  with chromadb's 0.65b0 and makes `pip install -r requirements.txt` unresolvable
  on a clean machine (it only "worked" locally via a forced install). httpx is
  already a dep; dropping the SDK removes the conflict for good.
- OTEL: chromadb needs the opentelemetry stack aligned at 1.44.0 (api+sdk+
  semantic-conventions==0.65b0) — now conflict-free since mistralai is gone. If a
  fresh install ever fails with `_ON_EMIT_RECURSION_COUNT_KEY`, that's an api/sdk
  version mismatch; align all otel packages to 1.44.0.
- chroma EmbeddingFunction interface (1.5.x): __call__ + embed_query + static
  name() + get_config(); default embeddings download all-MiniLM-L6-v2 (~80MB)
  to ~/.cache/chroma on first real run. Tests inject a fake embedder.
- MEMORY IS EPHEMERAL in v1: chromadb PersistentClient crashes on query with
  "Error creating hnsw segment reader: Nothing found on disk" under real
  timing (Windows disk-flush race). Persistent memory = P1 (save/load). --db
  persists sqlite world state; memory re-seeds each run. Tests use ephemeral
  chroma + a unique collection_prefix per store for isolation (EphemeralClient
  shares global state) — also keeps the suite fast (no disk).
- chromadb (local persistent client, default embeddings), sqlite3 stdlib,
  fastapi==0.139.2 + sse-starlette==3.4.5 + uvicorn==0.51.0, pydantic v2.
- RUN THE APP (Day 6): backend `.venv\Scripts\python -m uvicorn api.main:app
  --port 8000`; frontend `cd web && npm run dev` (Next 14, http://localhost:3000,
  NEXT_PUBLIC_API in web/.env.local). POST /tick is SSE (per-phase progress);
  the tick runs in a worker thread so /state stays responsive. db.py connection
  is cross-thread (check_same_thread=False) + lock-serialized for this.
- LLMs: Groq llama-3.3-70b-versatile for DIALOGUE + NARRATOR (speed/quality),
  Mistral mistral-small-latest for BATCHED PLANNING + importance scoring (JSON
  reliability, separate quota pool). All via sim/llm/client.py with backoff,
  fallback (groq↔mistral), and the per-day budget counter.
- Frontend: Next.js 14 + Tailwind. Town map is a raw <canvas> 2D game renderer
  (requestAnimationFrame loop; code-defined pixel-art sprites/tiles baked to
  offscreen canvases) in web/components/town/. Still NO Phaser/game-engine lib.
  (Owner decision — supersedes the original "SVG map / animation beyond tween
  out-of-scope" constraint; walk-cycle sprites + moving characters are in.)
- Game-feel layer (all procedural on the loop, no new deps): worldModel.ts has
  idle micro-wander + 4-dir facing + roaming critters (cat/chicken/bird);
  sprites.ts drawCharacter takes a `dir`; scene.ts adds sunlight tint, drifting
  cloud shadows, chimney smoke, swaying bushes; emotes.ts floats mood/gossip
  emoji (mood comes from a `mood` field GET /state derives from relationships);
  TownCanvas.tsx owns camera (wheel-zoom-about-cursor + drag-pan + follow-
  selected + reset — hit-testing inverts the same transform); audio.ts is
  synthesized Web Audio (ambient/footstep/click/chime), default muted, inits on
  the mute-button gesture. reduced-motion disables wander/emotes/particles.
- After install, record exact versions here + requirements.txt. Verify
  LangGraph and chromadb APIs against installed versions before coding.

## Repo layout
ghost-town/
  docs/PRD.md
  sim/
    world.py           # authoritative state: agents, zones, tick, events
    tick.py            # langgraph per-tick graph
    personas.py        # the 8 seed agents (see Seeding below)
    phases/
      plan.py          # batched planning call + anti-bleed validation
      act.py           # pure python action application
      converse.py      # pairing heuristic + dialogue calls + transfers
      remember.py      # memory writes, importance scoring
      narrate.py       # story log entry
      memory.py          # chromadb streams, retrieval scoring, reflections
  llm/client.py
  models.py          # pydantic: AgentPlan, Dialogue, MemoryEntry, ...
  db.py              # sqlite world state + story log
  cli.py             # run N ticks headless, print map + log
  tests/
  api/main.py          # fastapi: state, tick advance, SSE, inspector, events
  web/                 # next.js UI
  .env.example

## Env vars
GROQ_API_KEY, MISTRAL_API_KEY. Optional GHOST_DB (sqlite world-state path;
default :memory:; memory/chroma is ephemeral regardless — persistent = P1).

## Deploy (Day 7)
API → Render free (render.yaml), web → Vercel (root=web/, NEXT_PUBLIC_API=API
url). Free tier resets sqlite+memory on redeploy/idle-spindown and cold-starts
~30-60s (PRD §10). Steps + caveats in DEPLOY.md; pitch/architecture/writeup in
README.md; 2-min video shot list in DEMO.md.

## Seeding (PRD §9 Day-7 tip — bake it in from Day 1)
8 agents with FLAMMABLE relations: merchant owes farmer money; baker and
blacksmith rival for the café owner's attention; the well-keeper knows an old
secret about the mine; two natural gossips with high sociability. Personas in
personas.py as data, not prose blobs: name, occupation, home_zone, traits,
daily_goals, secrets[], initial_relationships[].
Zones (8): homes, cafe, market, farm, well, square, bakery, forge.

## Conventions
- Determinism aids: seed random; all heuristics (conversation pairing,
  movement) pure functions with unit tests.
- Every LLM JSON output → pydantic validation → one retry with error feedback.
- Log every LLM call: purpose, model, tokens, latency; per-tick cost summary.
- Tests: anti-bleed validator, retrieval scoring math, transfer extraction,
  budget degradation, pairing heuristic. Mock all LLM calls in tests.
- Story log entries ≤ 3 sentences, present tense, readable by non-tech people.

## Out of scope v1 (do not build)
Pathfinding/animation beyond zone teleport + CSS tween, voice, sprites/assets
generation, multiplayer, save/load UI (P1), talk-to-agent chat (P1).

## Gossip demo (Day-4 centerpiece)
`python -m sim.gossip_demo [agent] [ticks]` (default: tilda, 12) injects a
distinctive secret into ONE agent, runs live, prints the propagation chain
(exact wording per hop, mutations included), asserts it reached >= 2 others.
Spread relies on: evening-gathering nudge (whole town -> square in the evening
slot), pairing cooldown (a pair benched PAIR_COOLDOWN_TICKS after talking, so
gossip reaches new ears), transfer grounding + dedup, MAX_CONVERSATIONS_PER_TICK
=3. Demo sets GHOST_SCORE=0 to skip importance scoring (one fewer LLM call).
NOTE: free-tier providers throttle intermittently (30-60s/call) — a 12-tick run
can take 5-20 min; run it backgrounded.

## Working style
- Plan per phase → my approval → build. Commit per milestone.
- Console-first: the simulation must be fully runnable and debuggable headless
  via cli.py before any web work (Days 1–5 = headless).
- DAY-5 CHECKPOINT RULE (PRD §10): if conversations + gossip transfer aren't
  working by Day 5 morning, we CUT reflections (F6). Remind me of this rule
  if we're behind.
- If token budgets or library versions force a design change, stop and give
  me options — don't silently restructure.