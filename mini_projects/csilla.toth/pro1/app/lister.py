from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

import openai
import os


class ParticipantLister(ABC):
    @abstractmethod
    def list_names(self, text: str) -> List[str]:
        """Return a list of distinct person names found in `text`."""


class OpenAIListParticipants(ParticipantLister):
    """Uses OpenAI to extract person names from text and return a deduplicated list."""

    def __init__(self, model: str = "gpt-3.5-turbo"):
        self.model = model

    def list_names(self, text: str) -> List[str]:
        prompt = (
            "Extract all PERSON NAMES mentioned in the text below. Each name may consist of multiple words. "
            "Ignore phrases that are not person names such as verbs or adjectives. Only hungarian names are accepted."
            "Return a JSON array of names only. Each name should enlisted only once.\n\nText:\n" + text
        )
        # If no API key is set (env var or openai.api_key), skip remote call and fall back to a heuristic
        if not (os.getenv("OPENAI_API_KEY") or getattr(openai, "api_key", None)):
            content = ""
        else:
            try:
                client = openai.OpenAI()
                resp = client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=200,
                )
                content = resp.choices[0].message.content.strip()
            except Exception as e:
                print("Warning: name extraction failed, using local fallback.", e)
                content = ""
        # Try to parse JSON-like array, but be defensive
        import json
        import unicodedata

        def _normalize(n: str) -> str:
            # Normalize unicode, collapse whitespace and casefold for comparison
            s = unicodedata.normalize("NFKC", n).strip()
            s = " ".join(s.split())
            return s.casefold()

        try:
            names = json.loads(content) if content else []
            if isinstance(names, list):
                dedup = {}
                for n in names:
                    if not isinstance(n, str):
                        continue
                    orig = n.strip()
                    if not orig:
                        continue
                    key = _normalize(orig)
                    if key not in dedup:
                        dedup[key] = orig
                return list(dedup.values())
        except Exception:
            # Fallback heuristics: find capitalized word sequences
            pass
        # Fallback heuristic: simple capitalized token sequences
        words = text.replace('\n', ' ').split()
        candidates = []
        cur = []
        for w in words:
            if w.istitle():
                cur.append(w.strip('.,;:'))
            else:
                if cur:
                    candidates.append(" ".join(cur))
                    cur = []
        if cur:
            candidates.append(" ".join(cur))
        # Deduplicate preserving order using normalization
        dedup = {}
        for c in candidates:
            if not c:
                continue
            orig = c.strip()
            if not orig:
                continue
            key = _normalize(orig)
            if key not in dedup:
                dedup[key] = orig
        return list(dedup.values())
