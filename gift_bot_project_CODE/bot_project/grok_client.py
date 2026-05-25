"""
Grok API client (xAI).
Documentation: https://docs.x.ai/api
"""

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

GROK_API_KEY = os.getenv("GROK_API_KEY", "")
GROK_MODEL = os.getenv("GROK_MODEL", "grok-2-latest")
GROK_URL = "https://api.x.ai/v1/chat/completions"

TIMEOUT = 60.0


async def call_grok(prompt: str, temperature: float = 0.7) -> str:
    """Send a prompt to Grok and return the text answer."""
    if not GROK_API_KEY:
        raise RuntimeError("GROK_API_KEY is missing. Set it in .env file.")

    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
    }

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(GROK_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
