def render_output(process_result: dict) -> str:
    lines = [
        f"Obserwacja: {process_result['observation']}",
        f"Hipoteza: {process_result['hypothesis']}",
        f"Weryfikacja: {process_result['verification']}",
        f"Wniosek: {process_result['conclusion']}",
    ]
    return "\n".join(lines)
