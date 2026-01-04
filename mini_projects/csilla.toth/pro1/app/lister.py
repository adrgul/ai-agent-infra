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
            "Extract all PERSON NAMES mentioned in the text below. "
            "Return a JSON array of unique names only.\n\nText:\n" + text
        )
        # If no API key is set, skip remote call and fall back to a heuristic
        if not os.getenv("OPENAI_API_KEY"):
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
                    print("Warning: name extraction failed, using local fallback.")
                content = ""
        # Try to parse JSON-like array, but be defensive
        import json

        try:
            names = json.loads(content) if content else []
            if isinstance(names, list):
                return list(dict.fromkeys([n.strip() for n in names if isinstance(n, str) and n.strip()]))
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
        # Deduplicate preserving order
        seen = set()
        out = []
        for c in candidates:
            if c and c not in seen:
                seen.add(c)
                out.append(c)
        return out
