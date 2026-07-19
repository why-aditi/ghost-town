"""Shared tokenizer for grounding checks (anti-bleed planning + transfer
grounding). Distinctive lowercase words used for cheap knowledge-overlap tests.
"""
import re

STOP = {"that", "this", "with", "from", "they", "them", "their", "have",
        "will", "about", "into", "been", "were", "your", "what", "when",
        "then", "here", "there", "keep", "want", "need", "goes", "going",
        "today", "morning", "afternoon", "evening", "town", "resident",
        "told", "said", "talked", "learned", "heard"}


def tokens(*texts: str) -> set[str]:
    """Distinctive lowercase words (>=4 chars, minus stopwords)."""
    out: set[str] = set()
    for t in texts:
        for w in re.findall(r"[a-z']+", (t or "").lower()):
            if len(w) >= 4 and w not in STOP:
                out.add(w)
    return out
