# Optional LLM (Groq or Gemini)

import hashlib
import json
import logging
import re
from typing import Optional

import httpx
from sqlmodel import Session

from ..config import LLM_API_KEY, LLM_MODEL, LLM_PROVIDER, llm_enabled
from ..db import LlmCache, engine

log = logging.getLogger("clauseguard.llm")

DEFAULT_MODELS = {"groq": "llama-3.1-8b-instant", "gemini": "gemini-2.0-flash"}


def _call(system: str, user: str) -> str:
    model = LLM_MODEL or DEFAULT_MODELS[LLM_PROVIDER]
    if LLM_PROVIDER == "groq":
        r = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {LLM_API_KEY}"},
            json={"model": model, "temperature": 0.1, "max_tokens": 400,
                  "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
            timeout=25,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    r = httpx.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        headers={"x-goog-api-key": LLM_API_KEY},
        json={"systemInstruction": {"parts": [{"text": system}]},
              "contents": [{"role": "user", "parts": [{"text": user}]}],
              "generationConfig": {"temperature": 0.1, "maxOutputTokens": 400}},
        timeout=25,
    )
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


# ask the LLM, or return None if it is not set up
def complete(system: str, user: str, use_cache: bool = True) -> Optional[str]:
    if not llm_enabled():
        return None
    key = hashlib.sha256(f"{LLM_PROVIDER}|{system}|{user}".encode("utf-8")).hexdigest()
    if use_cache:
        with Session(engine) as s:
            hit = s.get(LlmCache, key)
            if hit:
                return hit.response
    try:
        reply = _call(system, user)
    except Exception as exc:
        # never log the API key
        log.warning("LLM call failed (%s)", type(exc).__name__)
        return None
    if use_cache:
        with Session(engine) as s:
            s.merge(LlmCache(hash=key, response=reply))
            s.commit()
    return reply


def parse_json(reply: Optional[str]) -> Optional[dict]:
    if not reply:
        return None
    m = re.search(r"\{.*\}", reply, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
