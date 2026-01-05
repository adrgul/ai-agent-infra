from typing import Any, List
import asyncio

from langchain_core.messages import BaseMessage
from openai import OpenAI

from ..core.config import settings


class LLMClient:
    """Wrapper around OpenAI APIs with fallback if responses API unavailable."""

    def __init__(self, client: OpenAI | None = None) -> None:
        self.client = client or OpenAI(api_key=settings.openai_api_key)

    async def generate(
        self, system_prompt: str, user_prompt: str, history: List[BaseMessage]
    ) -> str:
        messages = []
        messages.append({"role": "system", "content": system_prompt})
        messages.extend(self._to_openai_messages(history))
        messages.append({"role": "user", "content": user_prompt})

        responses_api = getattr(self.client, "responses", None)
        if responses_api:
            try:
                response = await asyncio.to_thread(
                    responses_api.create,
                    model=settings.model_name,
                    input=messages,
                )
                if getattr(response, "output_text", None):
                    return response.output_text
                for item in getattr(response, "output", []) or []:
                    content = getattr(item, "content", None)
                    if not content:
                        continue
                    for part in content:
                        text = getattr(part, "text", None)
                        if text:
                            return text
            except Exception:
                pass

        # Fallback to chat completions
        completion = await asyncio.to_thread(
            self.client.chat.completions.create,
            model=settings.model_name,
            messages=messages,
        )
        return completion.choices[0].message.content or ""

    def _to_openai_messages(self, history: List[BaseMessage]) -> List[dict[str, Any]]:
        converted: List[dict[str, Any]] = []
        for msg in history:
            role = "user"
            if getattr(msg, "type", "") == "ai":
                role = "assistant"
            converted.append({"role": role, "content": msg.content})
        return converted
