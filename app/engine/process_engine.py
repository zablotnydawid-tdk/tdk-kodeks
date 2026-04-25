from app.engine.steps import (
    build_conclusion,
    build_hypothesis,
    build_observation,
    build_verification,
)


def run_process(normalized_text: str, selected_mask: str) -> dict:
    observation = build_observation(normalized_text, selected_mask)
    hypothesis = build_hypothesis(normalized_text, selected_mask, observation)
    verification = build_verification(normalized_text, selected_mask, hypothesis)
    conclusion = build_conclusion(
        normalized_text,
        selected_mask,
        observation,
        hypothesis,
        verification,
    )

    return {
        "mask": selected_mask,
        "observation": observation,
        "hypothesis": hypothesis,
        "verification": verification,
        "conclusion": conclusion,
    }
