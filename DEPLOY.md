# Deploying Ghost Town

Two pieces: the **FastAPI backend** (Render) and the **Next.js web UI** (Vercel).
Both have generous free tiers. Total cost: ₹0.

## 1. Backend → Render

1. Push this repo to GitHub.
2. Render → **New → Blueprint**, point it at the repo. It reads `render.yaml`
   (a free Python web service running `uvicorn api.main:app`).
3. In the service's **Environment**, set `GROQ_API_KEY` and `MISTRAL_API_KEY`.
4. Deploy. Note the URL, e.g. `https://ghost-town-api.onrender.com`.

**Free-tier caveats (by design, per PRD §10):**
- **Everything resets on redeploy / idle spin-down.** World state (sqlite) and
  the memory stream (chroma) are ephemeral — the town re-seeds each boot.
  Persistent memory is a P1 feature (the chroma persistent client has a known
  Windows/disk HNSW bug; v1 keeps memory in-process).
- **Cold start ~30–60s** after ~15 min idle (free instances sleep). The first
  request after a sleep — and the first tick after boot (it downloads the ~80MB
  embedding model) — is slow.
- **One shared simulation** in memory (fine for a demo, not multi-user).

Want world-state to survive restarts? Upgrade to a paid instance, attach a
disk, and set `GHOST_DB=/var/data/ghost.sqlite` (the API reads that env). Memory
still resets.

## 2. Web UI → Vercel

1. Vercel → **New Project** → import the repo.
2. Set **Root Directory = `web`** (Vercel auto-detects Next.js 14).
3. Add env var **`NEXT_PUBLIC_API`** = your Render API URL (from step 1.4).
4. Deploy. Open the Vercel URL — it drives the Render API.

CORS is already open on the API (`allow_origins=["*"]`), so no extra config.

## Local dev
```bash
# backend (port 8000)
.venv\Scripts\python -m uvicorn api.main:app --port 8000
# frontend (port 3000) — web/.env.local: NEXT_PUBLIC_API=http://127.0.0.1:8000
cd web && npm run dev
```
