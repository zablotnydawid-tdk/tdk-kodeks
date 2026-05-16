import re


def build_report(raw_input: str, selected_mask: str, process_result: dict | None) -> str:
    data = _extract_energy_data(raw_input)
    calculations = _extract_calculations(process_result)
    efficiency = _extract_efficiency(process_result)
    recommendation = _build_recommendation(efficiency)

    return "\n".join(
        [
            "=== RAPORT WSTĘPNEJ ANALIZY ENERGII TDK&ProService ===",
            "",
            "1. DANE DO ANALIZY",
            *_format_input_data(data),
            "",
            "2. WYNIK OBLICZEŃ",
            *_format_calculations(calculations),
            "",
            "3. INTERPRETACJA",
            *_format_interpretation(efficiency),
            "",
            "4. CO MOŻE BYĆ PROBLEMEM",
            *_build_possible_causes(efficiency, data),
            "",
            "5. ZALECENIE",
            recommendation,
            "",
            "6. NASTĘPNY KROK",
            *_build_next_steps(data),
            "",
            "7. ZAŁOŻENIA I RYZYKA ANALIZY",
            *_build_risk_notes(),
            "",
            "8. KONTAKT",
            "TDK&ProService",
            "kontakt@tdkproservice.pl",
            "",
            _build_cta(),
        ]
    )


def _extract_energy_data(raw_input: str) -> dict:
    text = raw_input.lower().replace(",", ".")

    return {
        "consumption_kwh": _find_number(
            text,
            (
                r"zużycie\s+(\d+(?:\.\d+)?)",
                r"zuzycie\s+(\d+(?:\.\d+)?)",
                r"(\d+(?:\.\d+)?)\s*kwh",
            ),
        ),
        "price_per_kwh": _find_number(
            text,
            (
                r"cena\s+(\d+(?:\.\d+)?)",
                r"(\d+(?:\.\d+)?)\s*zł",
                r"(\d+(?:\.\d+)?)\s*zl",
            ),
        ),
        "pv_power_kw": _find_number(
            text,
            (
                r"pv\s+(\d+(?:\.\d+)?)",
                r"moc\s+(\d+(?:\.\d+)?)",
                r"(\d+(?:\.\d+)?)\s*kwp",
                r"(\d+(?:\.\d+)?)\s*kw(?!h)",
            ),
        ),
        "pv_monthly_production_kwh": _find_number(
            text,
            (
                r"produkcja(?:\s+pv)?\s+(\d+(?:\.\d+)?)",
                r"produkcja.*?(\d+(?:\.\d+)?)\s*kwh",
            ),
        ),
    }


def _extract_calculations(process_result: dict | None) -> dict:
    process_result = process_result or {}

    direct = process_result.get("calculations")
    if isinstance(direct, dict):
        return direct

    text = _combined_process_text(process_result).lower().replace(",", ".")

    return {
        "cost_without_pv": _find_number(
            text,
            (
                r"koszt bez pv\s*=\s*(\d+(?:\.\d+)?)",
                r"koszt bez pv to\s+(\d+(?:\.\d+)?)",
            ),
        ),
        "cost_after_pv": _find_number(
            text,
            (
                r"koszt po pv\s*=\s*(\d+(?:\.\d+)?)",
                r"koszt po pv to\s+(\d+(?:\.\d+)?)",
            ),
        ),
        "savings": _find_number(
            text,
            (
                r"oszczędność\s*=\s*(\d+(?:\.\d+)?)",
                r"oszczędność wynosi\s+(\d+(?:\.\d+)?)",
            ),
        ),
    }


def _extract_efficiency(process_result: dict | None) -> str | None:
    process_result = process_result or {}

    direct = process_result.get("interpretation") or process_result.get("efficiency")
    if isinstance(direct, str):
        return direct.lower()

    text = _combined_process_text(process_result).lower()
    for value in ("niska efektywność", "umiarkowana efektywność", "wysoka efektywność"):
        if value in text:
            return value

    return None


def _build_recommendation(efficiency: str | None) -> str:
    if efficiency == "niska efektywność":
        return (
            "W pierwszej kolejności warto sprawdzić taryfę, profil zużycia oraz godziny pracy "
            "największych odbiorników energii. Niski wynik może oznaczać, że instalacja lub sposób "
            "korzystania z energii nie wykorzystuje pełnego potencjału PV."
        )

    if efficiency == "umiarkowana efektywność":
        return (
            "Największy sens ma poprawa autokonsumpcji, sterowania urządzeniami oraz dopasowania "
            "pracy instalacji do codziennego zużycia. Warto również sprawdzić sposób rozliczania "
            "energii oraz dane z falownika."
        )

    if efficiency == "wysoka efektywność":
        return (
            "Wstępny wynik jest korzystny, jednak aby potwierdzić rzeczywistą efektywność "
            "i wykluczyć ukryte straty, zalecana jest pełna analiza techniczna oparta "
            "na danych rzeczywistych, fakturach i historii pracy instalacji."
        )

    return (
        "Do rzetelnej rekomendacji potrzebne jest uzupełnienie danych o zużyciu, cenie energii, "
        "mocy PV i miesięcznej produkcji. Bez kompletu danych raport należy traktować wyłącznie "
        "jako wstępną informację."
    )


def _format_input_data(data: dict) -> list[str]:
    return [
        f"- Zużycie miesięczne: {_format_value(data['consumption_kwh'], 'kWh')}",
        f"- Cena energii: {_format_value(data['price_per_kwh'], 'zł/kWh')}",
        f"- Moc instalacji PV: {_format_value(data['pv_power_kw'], 'kWp')}",
        f"- Miesięczna produkcja PV: {_format_value(data['pv_monthly_production_kwh'], 'kWh')}",
    ]


def _format_calculations(calculations: dict) -> list[str]:
    return [
        f"- Szacowany koszt bez PV: {_format_value(calculations.get('cost_without_pv'), 'zł')}",
        f"- Szacowany koszt po kompensacji PV: {_format_value(calculations.get('cost_after_pv'), 'zł')}",
        f"- Szacowana różnica miesięczna: {_format_value(calculations.get('savings'), 'zł')}",
    ]


def _format_interpretation(efficiency: str | None) -> list[str]:
    if efficiency == "niska efektywność":
        meaning = (
            "Oszczędność jest niewielka, więc instalacja, rozliczenie lub sposób korzystania "
            "z energii prawdopodobnie wymaga dokładniejszej weryfikacji."
        )
    elif efficiency == "umiarkowana efektywność":
        meaning = (
            "System daje zauważalny efekt, ale nadal może mieć rezerwę w autokonsumpcji, "
            "sterowaniu zużyciem albo sposobie rozliczania energii."
        )
    elif efficiency == "wysoka efektywność":
        meaning = (
            "Wynik jest korzystny, jednak opiera się wyłącznie na danych wstępnych. "
            "W praktyce instalacja może nadal generować ukryte straty wynikające z konfiguracji, "
            "autokonsumpcji, taryfy lub sposobu rozliczania."
        )
    else:
        meaning = (
            "Brakuje kompletu danych, dlatego wynik należy traktować jako wstępny "
            "i wymagający doprecyzowania."
        )

    return [
        f"- Poziom efektywności: {efficiency or 'nieokreślony'}",
        f"- Znaczenie dla klienta: {meaning}",
    ]


def _build_possible_causes(efficiency: str | None, data: dict) -> list[str]:
    causes = [
        "- Zbyt mała autokonsumpcja energii z PV w godzinach produkcji.",
        "- Taryfa lub sposób rozliczania niedopasowane do profilu zużycia.",
        "- Konfiguracja falownika, pompy ciepła lub sterowania może wymagać korekty.",
    ]

    if data.get("pv_monthly_production_kwh") is None:
        causes.append("- Brak danych o produkcji PV utrudnia ocenę realnej pracy instalacji.")
    elif efficiency in ("niska efektywność", "umiarkowana efektywność"):
        causes.append(
            "- Warto sprawdzić, czy magazyn energii lub zmiana harmonogramu pracy urządzeń "
            "poprawi wykorzystanie PV."
        )

    return causes[:4]


def _build_next_steps(data: dict) -> list[str]:
    missing = []

    if data.get("consumption_kwh") is None:
        missing.append("- Miesięczne zużycie energii w kWh.")
    if data.get("price_per_kwh") is None:
        missing.append("- Cena 1 kWh z faktury lub taryfy.")
    if data.get("pv_power_kw") is None:
        missing.append("- Moc instalacji PV.")
    if data.get("pv_monthly_production_kwh") is None:
        missing.append("- Produkcja PV z ostatniego miesiąca.")

    base = [
        "- Ostatnia faktura za energię.",
        "- Dane z aplikacji falownika lub licznika produkcji.",
        "- Informacja o taryfie i sposobie rozliczania prosumenta.",
        "- Informacja, czy w budynku pracuje pompa ciepła lub magazyn energii.",
    ]

    if missing:
        return ["Dane do uzupełnienia:", *missing, "Dane pomocnicze:", *base]

    return base


def _build_risk_notes() -> list[str]:
    return [
        "- Raport oparty jest na danych deklarowanych przez użytkownika.",
        "- Rzeczywista efektywność może różnić się od wyniku w zależności od taryfy, autokonsumpcji, ustawień instalacji i sposobu rozliczania.",
        "- Wynik nie stanowi pełnego audytu technicznego ani opinii rzeczoznawczej.",
        "- Pełna diagnostyka wymaga analizy faktur, danych z urządzeń oraz sposobu pracy instalacji w czasie.",
    ]


def _build_cta() -> str:
    return (
        "Jeśli chcesz sprawdzić, czy instalacja rzeczywiście pracuje optymalnie "
        "i czy nie generuje ukrytych strat, skontaktuj się z TDK&ProService.\n"
        "Analiza wykonywana jest indywidualnie na podstawie danych rzeczywistych."
    )


def _find_number(text: str, patterns: tuple[str, ...]) -> float | None:
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return float(match.group(1))
    return None


def _format_value(value: float | None, unit: str) -> str:
    if value is None:
        return "brak danych"
    return f"{value:g} {unit}"


def _combined_process_text(process_result: dict | None) -> str:
    process_result = process_result or {}

    return "\n".join(
        str(process_result.get(key, ""))
        for key in ("observation", "hypothesis", "verification", "conclusion", "recommendation")
    )