from groq import Groq
from app.config import settings
import json

client = Groq(api_key=settings.GROQ_API_KEY)


def call_groq(system_prompt: str, user_prompt: str, temperature: float = 0.7, max_tokens: int = 8000) -> str:
    """Call Groq LLM and return raw text response."""
    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


def call_groq_json(system_prompt: str, user_prompt: str, temperature: float = 0.3, max_tokens: int = 8000) -> dict:
    """Call Groq LLM and parse JSON response. Retries once on parse failure."""
    response_text = call_groq(system_prompt, user_prompt, temperature, max_tokens)

    # Clean response — remove markdown code blocks if present
    cleaned = response_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Retry with stricter prompt
        retry_prompt = (
            f"Your previous response was not valid JSON. "
            f"Return ONLY valid JSON with no markdown formatting.\n\n{user_prompt}"
        )
        retry_text = call_groq(system_prompt, retry_prompt, temperature=0.1, max_tokens=max_tokens)
        retry_cleaned = retry_text.strip()
        if retry_cleaned.startswith("```json"):
            retry_cleaned = retry_cleaned[7:]
        if retry_cleaned.startswith("```"):
            retry_cleaned = retry_cleaned[3:]
        if retry_cleaned.endswith("```"):
            retry_cleaned = retry_cleaned[:-3]
        return json.loads(retry_cleaned.strip())


def call_groq_chat(messages: list, system_prompt: str) -> str:
    """Call Groq LLM for multi-turn chat."""
    full_messages = [{"role": "system", "content": system_prompt}] + messages
    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=full_messages,
        temperature=0.7,
        max_tokens=2000,
    )
    return response.choices[0].message.content
