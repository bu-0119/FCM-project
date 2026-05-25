# Sensitive word filter placeholder. Replace with real implementation in production.

SENSITIVE_WORDS: set[str] = set()


def contains_sensitive(text: str) -> bool:
    if not SENSITIVE_WORDS:
        return False
    return any(word in text for word in SENSITIVE_WORDS)


def filter_sensitive(text: str) -> str:
    if not SENSITIVE_WORDS:
        return text
    result = text
    for word in SENSITIVE_WORDS:
        result = result.replace(word, "***")
    return result
