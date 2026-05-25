from openai import AsyncOpenAI

from app.config import settings

_llm_client: AsyncOpenAI | None = None


def get_llm_client() -> AsyncOpenAI | None:
    global _llm_client
    if not settings.llm_api_key:
        return None
    if _llm_client is None:
        _llm_client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
        )
    return _llm_client


async def llm_chat(messages: list[dict], temperature: float = 0.7, max_tokens: int = 500) -> str:
    """Send a chat completion request. Returns empty string on failure."""
    client = get_llm_client()
    if client is None:
        return ""
    try:
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception:
        return ""
