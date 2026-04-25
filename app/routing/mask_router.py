MASKS = (
    "Witness_EXIM",
    "CaseReporter",
    "ModelBuilder",
    "ExecManager",
)


def choose_mask(normalized_text: str) -> tuple[str, str]:
    text = normalized_text.lower()

    # 🔥 NOWE — PRIORYTET ENERGETYCZNY
    if any(keyword in text for keyword in (
        "kwh", "pv", "fotowoltaika", "prąd", "energia",
        "pompa ciepła", "rachunki", "zużycie", "taryfa", "produkcja"
    )):
        return "CaseReporter", "matched_energy_keywords"

    if any(keyword in text for keyword in ("widziałem", "obserwacja", "fakt", "zdarzenie", "świadek")):
        return "Witness_EXIM", "matched_observation_keywords"

    if any(keyword in text for keyword in ("zgłoszenie", "raport", "incydent", "sprawa", "problem")):
        return "CaseReporter", "matched_case_keywords"

    if any(keyword in text for keyword in ("model", "struktura", "architektura", "system", "projekt")):
        return "ModelBuilder", "matched_model_keywords"

    if any(keyword in text for keyword in ("wykonaj", "plan", "zadanie", "decyzja", "zarządzaj")):
        return "ExecManager", "matched_execution_keywords"

    return "Witness_EXIM", "default_mask"