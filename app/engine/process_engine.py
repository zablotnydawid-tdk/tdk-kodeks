from app.engine.steps import (
    build_conclusion,
    build_hypothesis,
    build_observation,
    build_verification,
    calculate_energy_case,
    extract_energy_data,
    is_energy_case,
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
    calculations = None
    if selected_mask == "CaseReporter" and is_energy_case(normalized_text):
        calculations = calculate_energy_case(extract_energy_data(normalized_text))

    return {
        "mask": selected_mask,
        "observation": observation,
        "hypothesis": hypothesis,
        "verification": verification,
        "conclusion": conclusion,
        "calculations": calculations,
    }
