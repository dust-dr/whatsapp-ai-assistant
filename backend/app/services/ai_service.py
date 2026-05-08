import httpx
from app.core.config import settings

# Available Groq models for this project:
# - llama-3.1-8b-instant    → fast, good for MVP
# - llama-3.3-70b-versatile → smarter, better for production
GROQ_DEFAULT_MODEL = "llama-3.1-8b-instant"


async def generate_reply(system_prompt: str, user_message: str) -> str:
    """
    Main function called by all endpoints.
    Automatically uses Groq or Ollama based on .env setting.
    """
    if settings.ai_provider == "groq":
        return await _call_groq(system_prompt, user_message)
    elif settings.ai_provider == "ollama":
        return await _call_ollama(system_prompt, user_message)
    else:
        raise ValueError(f"Unknown AI provider: {settings.ai_provider}")


async def _call_groq(system_prompt: str, user_message: str) -> str:
    """
    Calls Groq API.
    Uses model from .env if set, otherwise uses GROQ_DEFAULT_MODEL.
    """
    model = settings.groq_model if settings.groq_model else GROQ_DEFAULT_MODEL

    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json"
    }

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message}
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=body,
            timeout=30.0
        )

        if response.status_code != 200:
            print(f"Groq error {response.status_code}: {response.text}")

        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def _call_ollama(system_prompt: str, user_message: str) -> str:
    """
    Calls Ollama running locally.
    Backup option for offline/private deployments.
    """
    body = {
        "model": settings.ollama_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message}
        ],
        "stream": False
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.ollama_base_url}/api/chat",
            json=body,
            timeout=60.0
        )
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]
