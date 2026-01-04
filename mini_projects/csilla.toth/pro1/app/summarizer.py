from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

import openai
import os


class Summarizer(ABC):
    @abstractmethod
    def summarize(self, text: str, max_words: int = 20) -> str:
        """Return a short summary of `text` containing at most `max_words` words."""


class OpenAISummarizer(Summarizer):
    """Summarizer implementation that uses the OpenAI Chat API.

    This class is small and focused (SRP). It depends only on the openai
    client and a model name injected by the caller (DIP).
    """

    def __init__(self, model: str = "gpt-3.5-turbo"):
        self.model = model

    def summarize(self, text: str, max_words: int = 20) -> str:
        prompt = (
            "You are a concise summarizer. "
            f"Summarize the following text in at most {max_words} words. "
            "Return only the summary text, no extra commentary.\n\nText:\n" + text
        )
        # If no API key is available, skip remote call and use a simple fallback
        if not os.getenv("OPENAI_API_KEY"):
            parts = text.split()
            return " ".join(parts[:max_words])

        try:
            client = openai.OpenAI()
            resp = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=120,
            )
            # new client returns choices with message object
            summary = resp.choices[0].message.content.strip()
            # Ensure we don't exceed max_words by truncation as a fallback.
            parts = summary.split()
            if len(parts) <= max_words:
                return summary
            return " ".join(parts[:max_words]).rstrip(".,;:")
        except Exception:
            print("Warning: summarization failed, using local fallback.")
            # Fallback: naive first N words from the original text
            return " ".join(text.split()[:max_words])
