from __future__ import annotations

from dataclasses import dataclass


KNOWLEDGE_DOMAINS = (
    "REGULATORY",
    "TECHNICAL",
    "FIELD_PROCEDURE",
    "FINANCIAL",
    "SUBSIDY",
    "BILLING",
    "VPP_ALGORITHM",
    "CLIENT_EVIDENCE",
)


DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "REGULATORY": (
        "ustawa",
        "rozporzadzenie",
        "rozporządzenie",
        "regulacyj",
        "audyt",
        "ure",
        "csire",
        "obowiazek",
        "obowiązek",
    ),
    "TECHNICAL": (
        "falownik",
        "inverter",
        "napiecie",
        "napięcie",
        "253v",
        "pompa ciepla",
        "pompa ciepła",
        "bess",
        "ems",
        "hems",
    ),
    "FIELD_PROCEDURE": (
        "procedura",
        "krok",
        "sprawdz",
        "sprawdź",
        "pomiar",
        "diagnostyka",
        "serwis",
        "teren",
    ),
    "FINANCIAL": (
        "koszt",
        "pln",
        "zl",
        "zł",
        "faktura",
        "oplata",
        "opłata",
        "strata",
        "roi",
    ),
    "SUBSIDY": (
        "dotacja",
        "program",
        "moj prad",
        "mój prąd",
        "czyste powietrze",
        "oze 2026",
        "dofinansowanie",
    ),
    "BILLING": (
        "net-billing",
        "net billing",
        "taryfa",
        "rachunek",
        "rozliczenie",
        "csire",
        "sprzedaz energii",
        "sprzedaż energii",
    ),
    "VPP_ALGORITHM": (
        "vpp",
        "virtual power plant",
        "agregacja",
        "algorytm",
        "dispatch",
        "elastycznosc",
        "elastyczność",
        "sterowanie",
    ),
    "CLIENT_EVIDENCE": (
        "klient",
        "zdjecie",
        "zdjęcie",
        "zalacznik",
        "załącznik",
        "csv",
        "pomiar klienta",
        "screen",
        "zrzut",
    ),
}


@dataclass(frozen=True)
class DomainClassification:
    domain: str
    confidence: float
    matched_keywords: tuple[str, ...]


def classify_domain(text: str) -> DomainClassification:
    normalized = text.lower()
    matches: dict[str, list[str]] = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        found = [keyword for keyword in keywords if keyword in normalized]
        if found:
            matches[domain] = found

    if not matches:
        return DomainClassification("CLIENT_EVIDENCE", 0.35, ())

    best_domain, best_keywords = max(matches.items(), key=lambda item: len(item[1]))
    confidence = min(0.95, 0.45 + (0.1 * len(best_keywords)))
    return DomainClassification(best_domain, round(confidence, 2), tuple(best_keywords))
