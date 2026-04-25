def normalize_input(raw_text: str) -> str:
    parts = raw_text.strip().split()
    normalized = " ".join(parts)
    return normalized.lower()
