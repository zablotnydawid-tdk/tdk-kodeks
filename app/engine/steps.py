ENERGY_KEYWORDS = (
    "energia", "energetyczny", "energetyczna", "prąd", "pv",
    "fotowoltaika", "fotowoltaiczna", "pompa ciepła", "rachunki",
    "rachunek", "zużycie", "zuzycie", "kwh", "kwp", "kw",
    "zł", "zl", "taryfa", "moc", "produkcja", "cena",
)


def is_energy_case(normalized_text: str) -> bool:
    text = normalized_text.lower()
    return any(keyword in text for keyword in ENERGY_KEYWORDS)


def _tokenize_numbers(normalized_text: str) -> list[str]:
    text = normalized_text.lower().replace(",", ".")
    for char in (":", ";", "(", ")", "[", "]", "{", "}", "/", "\\", "=", "-"):
        text = text.replace(char, " ")
    return text.split()


def _parse_float(token: str) -> float | None:
    try:
        return float(token.strip())
    except ValueError:
        return None


def extract_number_before_keyword(normalized_text: str, keywords: tuple[str, ...]) -> float | None:
    tokens = _tokenize_numbers(normalized_text)
    for index, token in enumerate(tokens):
        if token in keywords and index > 0:
            value = _parse_float(tokens[index - 1])
            if value is not None:
                return value
    return None


def extract_number_after_keyword(normalized_text: str, keywords: tuple[str, ...]) -> float | None:
    tokens = _tokenize_numbers(normalized_text)
    for index, token in enumerate(tokens):
        if token in keywords:
            for next_token in tokens[index + 1:index + 4]:
                value = _parse_float(next_token)
                if value is not None:
                    return value
    return None


def extract_energy_data(normalized_text: str) -> dict:
    consumption_kwh = (
        extract_number_after_keyword(normalized_text, ("zużycie", "zuzycie"))
        or extract_number_before_keyword(normalized_text, ("kwh",))
    )
    price_per_kwh = (
        extract_number_after_keyword(normalized_text, ("cena",))
        or extract_number_before_keyword(normalized_text, ("zł", "zl"))
    )
    pv_power_kw = (
        extract_number_after_keyword(normalized_text, ("moc", "pv"))
        or extract_number_before_keyword(normalized_text, ("kw", "kwp"))
    )
    pv_monthly_production_kwh = (
        extract_number_after_keyword(normalized_text, ("produkcja",))
        or extract_number_before_keyword(normalized_text, ("kwh",))
    )

    return {
        "consumption_kwh": consumption_kwh,
        "price_per_kwh": price_per_kwh,
        "pv_power_kw": pv_power_kw,
        "pv_monthly_production_kwh": pv_monthly_production_kwh,
    }


def calculate_energy_case(data: dict) -> dict | None:
    required_values = (
        data["consumption_kwh"],
        data["price_per_kwh"],
        data["pv_monthly_production_kwh"],
    )
    if any(value is None for value in required_values):
        return None

    consumption_kwh = data["consumption_kwh"]
    price_per_kwh = data["price_per_kwh"]
    pv_monthly_production_kwh = data["pv_monthly_production_kwh"]

    cost_without_pv = consumption_kwh * price_per_kwh
    raw_cost_after_pv = max(consumption_kwh - pv_monthly_production_kwh, 0) * price_per_kwh

    # Model analizy wstępnej:
    # Wynik ma charakter ostrożnościowego szacunku kosztów po uwzględnieniu pracy instalacji PV.
    # System nie zakłada idealnego bilansowania energii ani pełnej kompensacji kosztów,
    # ponieważ rzeczywisty wynik zależy m.in. od autokonsumpcji, taryfy,
    # profilu zużycia, sposobu rozliczeń oraz pracy instalacji w czasie.
    # Dzięki temu raport zachowuje realistyczny i profesjonalny charakter
    # na etapie wstępnej analizy techniczno-ekonomicznej.
    residual_cost_floor = max(120, cost_without_pv * 0.20)
    cost_after_pv = max(raw_cost_after_pv, residual_cost_floor)
    savings = max(cost_without_pv - cost_after_pv, 0)

    if cost_after_pv >= cost_without_pv:
        efficiency_label = "niska efektywność"
    elif cost_after_pv <= cost_without_pv * 0.35:
        efficiency_label = "wysoka efektywność"
    else:
        efficiency_label = "umiarkowana efektywność"

    if raw_cost_after_pv == 0 or pv_monthly_production_kwh >= consumption_kwh:
        calculation_mode = "conservative_residual_estimate"
    else:
        calculation_mode = "standard_estimate_with_pv"

    return {
        "cost_without_pv": round(cost_without_pv, 2),
        "raw_cost_after_pv": round(raw_cost_after_pv, 2),
        "residual_cost_floor": round(residual_cost_floor, 2),
        "cost_after_pv": round(cost_after_pv, 2),
        "savings": round(savings, 2),
        "efficiency_label": efficiency_label,
        "calculation_mode": calculation_mode,
    }


def classify_energy_savings(savings: float) -> str:
    if savings < 50:
        return "niska efektywność"
    if savings <= 200:
        return "umiarkowana efektywność"
    return "wysoka efektywność"


def build_energy_recommendation(efficiency: str) -> str:
    if efficiency == "niska efektywność":
        return "Zalecenie: rozważ zmianę taryfy lub optymalizację zużycia."
    if efficiency == "umiarkowana efektywność":
        return "Zalecenie: rozważ poprawę autokonsumpcji lub sterowania."
    return "Zalecenie: system działa dobrze."


def missing_energy_fields(data: dict) -> list[str]:
    missing = []
    if data["consumption_kwh"] is None:
        missing.append("zużycie kWh miesięcznie")
    if data["price_per_kwh"] is None:
        missing.append("cena 1 kWh")
    if data["pv_power_kw"] is None:
        missing.append("moc PV")
    if data["pv_monthly_production_kwh"] is None:
        missing.append("miesięczna produkcja PV")
    return missing


def build_observation(normalized_text: str, selected_mask: str) -> str:
    if selected_mask == "CaseReporter" and is_energy_case(normalized_text):
        return (
            "Maska CaseReporter rozpoznała zgłoszenie dotyczące obszaru energetycznego, "
            "obejmujące zużycie energii, instalację PV, pompę ciepła albo rachunki."
        )

    return (
        f"Maska {selected_mask} przyjęła dane wejściowe o długości "
        f"{len(normalized_text)} znaków i rozpoznała główny kontekst wypowiedzi."
    )


def build_hypothesis(normalized_text: str, selected_mask: str, observation: str) -> str:
    if selected_mask == "Witness_EXIM":
        return "Tekst opisuje obserwację, zdarzenie lub stan wymagający uchwycenia faktów."

    if selected_mask == "CaseReporter":
        if is_energy_case(normalized_text):
            return (
                "Tekst wygląda jak zgłoszenie problemu energetycznego i może dotyczyć "
                "opłacalności PV, pracy pompy ciepła, wzrostu rachunków albo niezgodności "
                "między instalacją a realnym zużyciem energii."
            )
        return "Tekst wygląda jak zgłoszenie sprawy, incydentu albo problemu do uporządkowania."

    if selected_mask == "ModelBuilder":
        return "Tekst sugeruje potrzebę zbudowania modelu, struktury albo koncepcji systemu."

    if selected_mask == "ExecManager":
        return "Tekst wskazuje na potrzebę decyzji, wykonania planu albo koordynacji działania."

    return f"Nie rozpoznano specyficznej maski. Obserwacja bazowa: {observation}"


def build_verification(normalized_text: str, selected_mask: str, hypothesis: str) -> str:
    keyword_count = len(normalized_text.split())

    if selected_mask == "CaseReporter" and is_energy_case(normalized_text):
        data = extract_energy_data(normalized_text)
        calculations = calculate_energy_case(data)
        missing = missing_energy_fields(data)

        lines = [
            f"Hipoteza została zweryfikowana wstępnie przez wykrycie słów kluczowych z obszaru energii ({keyword_count} tokenów).",
            "Potrzebne dane:",
            "- zużycie kWh miesięcznie",
            "- cena 1 kWh",
            "- moc PV",
            "- miesięczna produkcja PV",
        ]

        if calculations is not None:
            efficiency = classify_energy_savings(calculations["savings"])
            recommendation = build_energy_recommendation(efficiency)
            lines.extend(
                [
                    "Obliczenia:",
                    f"- koszt bez PV = {calculations['cost_without_pv']} zł",
                    f"- koszt po PV = {calculations['cost_after_pv']} zł",
                    f"- oszczędność = {calculations['savings']} zł",
                    f"- interpretacja = {efficiency}",
                    f"- {recommendation}",
                ]
            )
        else:
            lines.append("Brakuje danych do pełnego wyliczenia:")
            for field in missing:
                lines.append(f"- {field}")

        return "\n".join(lines)

    return (
        f"Hipoteza została zweryfikowana wstępnie na podstawie słów kluczowych, "
        f"liczby tokenów ({keyword_count}) oraz zgodności z profilem maski {selected_mask}."
    )


def build_conclusion(
    normalized_text: str,
    selected_mask: str,
    observation: str,
    hypothesis: str,
    verification: str,
) -> str:
    if selected_mask == "CaseReporter" and is_energy_case(normalized_text):
        data = extract_energy_data(normalized_text)
        calculations = calculate_energy_case(data)
        missing = missing_energy_fields(data)

        if calculations is not None:
            efficiency = classify_energy_savings(calculations["savings"])
            recommendation = build_energy_recommendation(efficiency)
            return (
                "Wejście zostało przetworzone jako zgłoszenie energetyczne. "
                f"Szacowany koszt bez PV to {calculations['cost_without_pv']} zł, "
                f"koszt po PV to {calculations['cost_after_pv']} zł, "
                f"oszczędność wynosi {calculations['savings']} zł. "
                f"Ocena wyniku: {efficiency}. "
                f"{recommendation}"
            )

        return (
            "Wejście zostało przetworzone jako zgłoszenie energetyczne. "
            "Do wykonania pełnej analizy brakuje następujących danych: "
            + ", ".join(missing)
            + "."
        )

    return (
        f"Wejście zostało przetworzone przez maskę {selected_mask}. "
        f"Na podstawie obserwacji i weryfikacji system przyjmuje następującą interpretację: {hypothesis}"
    )
