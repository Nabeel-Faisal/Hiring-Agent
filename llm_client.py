"""
Unified async LLM client.
Wraps Groq (free) or Anthropic — set LLM_PROVIDER in .env.
"""
import os
from groq import AsyncGroq
from config import MODEL_GROQ, GROQ_API_KEY


class LLMClient:
    def __init__(self):
        self._groq = AsyncGroq(api_key=GROQ_API_KEY)

    async def chat(self, messages: list[dict], system: str = "", max_tokens: int = 2000) -> str:
        all_messages = []
        if system:
            all_messages.append({"role": "system", "content": system})
        all_messages.extend(messages)

        response = await self._groq.chat.completions.create(
            model=MODEL_GROQ,
            messages=all_messages,
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return response.choices[0].message.content


def make_client() -> LLMClient:
    return LLMClient()
