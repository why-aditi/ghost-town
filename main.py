"""Deploy shim: the app lives in api/main.py, but hosts that default to
`uvicorn main:app` (e.g. Render's autodetected start command) look for a
top-level `main:app`. Re-export it here so that just works.
"""
from api.main import app  # noqa: F401
