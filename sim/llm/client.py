"""LLM client: Groq + Mistral, JSON-mode + pydantic validation, backoff,
cross-provider fallback, and the per-day budget counter (CLAUDE.md).

Everything goes through complete_json / complete so logging, retries, and
fallback happen in one place. Provider functions are resolved at call time,
so tests monkeypatch `_mistral` / `_groq` / `complete_json` directly.
"""
import logging
import os
import time
from pathlib import Path

from pydantic import BaseModel, ValidationError

log = logging.getLogger("sim.llm")

# Model assignment per CLAUDE.md: Mistral plans/scores, Groq talks/narrates.
_DEFAULT_MODEL = {"mistral": "mistral-small-latest", "groq": "llama-3.3-70b-versatile"}
_FALLBACK = {"mistral": "groq", "groq": "mistral"}


class LLMUnavailable(RuntimeError):
    """Raised when a provider is unusable (missing key) or all providers fail."""


def _load_dotenv() -> None:
    # ponytail: 6-line stdlib loader beats adding python-dotenv.
    for p in (Path("sim/.env"), Path(".env")):
        if not p.exists():
            continue
        for line in p.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_dotenv()


# --- provider wrappers: (text, tokens) ---
def _mistral(prompt: str, model: str, temperature: float, json_mode: bool):
    from mistralai.client import Mistral
    key = os.getenv("MISTRAL_API_KEY")
    if not key:
        raise LLMUnavailable("MISTRAL_API_KEY not set")
    client = Mistral(api_key=key)
    kw = {"response_format": {"type": "json_object"}} if json_mode else {}
    r = client.chat.complete(
        model=model, temperature=temperature,
        messages=[{"role": "user", "content": prompt}], **kw)
    tokens = getattr(getattr(r, "usage", None), "total_tokens", None)
    return r.choices[0].message.content, tokens


def _groq(prompt: str, model: str, temperature: float, json_mode: bool):
    import groq
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise LLMUnavailable("GROQ_API_KEY not set")
    client = groq.Groq(api_key=key)
    kw = {"response_format": {"type": "json_object"}} if json_mode else {}
    r = client.chat.completions.create(
        model=model, temperature=temperature,
        messages=[{"role": "user", "content": prompt}], **kw)
    tokens = getattr(getattr(r, "usage", None), "total_tokens", None)
    return r.choices[0].message.content, tokens


def _provider_fn(name: str):
    # Resolved from module globals at call time → monkeypatchable in tests.
    return {"mistral": _mistral, "groq": _groq}[name]


def _is_rate_limit(e: Exception) -> bool:
    s = str(e).lower()
    return "429" in s or "resource_exhausted" in s or "rate limit" in s


def _with_backoff(fn, attempts: int = 3, base: float = 0.5):
    for i in range(attempts):
        try:
            return fn()
        except LLMUnavailable:
            raise  # config error (missing key) — retrying won't help; fall back instead
        except Exception as e:
            # Rate limit: same-provider retry is pointless (needs a long wait) —
            # fail fast so complete() falls back to the other provider.
            if _is_rate_limit(e) or i == attempts - 1:
                raise
            time.sleep(base * (2 ** i))  # ponytail: stdlib backoff, not tenacity


def _one_call(provider: str, purpose: str, prompt: str, model: str | None,
              temperature: float, json_mode: bool) -> str:
    model = model or _DEFAULT_MODEL[provider]
    fn = _provider_fn(provider)
    t0 = time.time()
    text, tokens = _with_backoff(lambda: fn(prompt, model, temperature, json_mode))
    log.info("llm call purpose=%s provider=%s model=%s tokens=%s latency=%.2fs",
             purpose, provider, model, tokens, time.time() - t0)
    return text


def complete(prompt: str, *, purpose: str, provider: str = "mistral",
             model: str | None = None, temperature: float = 0.2,
             json_mode: bool = True) -> str:
    """Call `provider`; on failure fall back to the other provider. Raises
    LLMUnavailable only if both fail. (Fallback uses the other provider's
    default model — a mistral model id won't run on groq.)"""
    last = None
    for i, p in enumerate((provider, _FALLBACK[provider])):
        try:
            return _one_call(p, purpose, prompt, model if i == 0 else None,
                             temperature, json_mode)
        except Exception as e:  # noqa: BLE001 - try the fallback provider
            last = e
            log.warning("provider %s failed for %s: %s", p, purpose,
                        str(e).splitlines()[0][:200])  # trim provider error dumps
    raise LLMUnavailable(f"all providers failed for {purpose}: {last}")


def complete_json(prompt: str, schema: type[BaseModel], *, purpose: str,
                  provider: str = "mistral", model: str | None = None,
                  temperature: float = 0.2) -> BaseModel:
    """complete() + pydantic validation + ONE retry with error feedback."""
    text = complete(prompt, purpose=purpose, provider=provider, model=model,
                    temperature=temperature)
    try:
        return schema.model_validate_json(text)
    except ValidationError as e:
        retry = (f"{prompt}\n\nYour previous reply was invalid JSON for the "
                 f"schema:\n{e}\nReturn ONLY valid JSON matching the schema.")
        text = complete(retry, purpose=f"{purpose}-retry", provider=provider,
                        model=model, temperature=temperature)
        return schema.model_validate_json(text)  # propagates if still invalid


class LLMBudget:
    """Per-simulated-day call counter. Degrades the tick to 'quiet' when the
    daily cap is reached (CLAUDE.md: <=60/day). Resets on day rollover."""

    def __init__(self, per_day: int = 60):
        self.per_day = per_day
        self._day: int | None = None
        self._count = 0

    def _roll(self, day: int) -> None:
        if day != self._day:
            self._day, self._count = day, 0

    def can_spend(self, day: int, n: int = 1) -> bool:
        self._roll(day)
        return self._count + n <= self.per_day

    def spend(self, day: int, n: int = 1) -> None:
        self._roll(day)
        self._count += n

    def spent(self, day: int) -> int:
        self._roll(day)
        return self._count
