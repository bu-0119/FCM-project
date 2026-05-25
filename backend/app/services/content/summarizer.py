from app.config import settings


async def summarize_content(title: str, body: str, llm_client=None) -> str:
    """Generate a Chinese summary of football content using LLM.
    Falls back to simple truncation if LLM is unavailable."""

    if body is None:
        body = ""

    if llm_client and settings.llm_api_key:
        try:
            response = await llm_client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个足球新闻摘要助手。用1-2句简洁的中文总结以下内容，保留关键人物和事件。",
                    },
                    {"role": "user", "content": f"标题: {title}\n内容: {body[:2000]}"},
                ],
                temperature=0.3,
                max_tokens=150,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            pass

    # Fallback: truncate and clean
    text = body or title
    # Remove HTML tags
    import re
    text = re.sub(r"<[^>]+>", "", text)
    text = text.strip()
    if len(text) > 200:
        text = text[:200] + "..."
    return text
