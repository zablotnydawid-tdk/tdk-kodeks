
from __future__ import annotations
from typing import Any

PL_NUMBER_WORDS = {
    "zero": 0, "jeden": 1, "jedna": 1, "dwa": 2, "dwie": 2, "trzy": 3, "cztery": 4, "piec": 5, "pięć": 5,
    "szesc": 6, "sześć": 6, "siedem": 7, "osiem": 8, "dziewiec": 9, "dziewięć": 9,
    "dziesiec": 10, "dziesięć": 10, "jedenascie": 11, "jedenaście": 11, "dwanascie": 12, "dwanaście": 12,
    "trzynascie": 13, "trzynaście": 13, "czternascie": 14, "czternaście": 14, "pietnascie": 15, "piętnaście": 15,
    "dwadziescia": 20, "dwadzieścia": 20, "trzydziesci": 30, "trzydzieści": 30, "czterdziesci": 40, "czterdzieści": 40,
    "piec dziesiat": 50, "pięćdziesiąt": 50, "szescdziesiat": 60, "sześćdziesiąt": 60, "siedemdziesiat": 70,
    "siedemdziesiąt": 70, "osiemdziesiat": 80, "osiemdziesiąt": 80, "dziewiecdziesiat": 90, "dziewięćdziesiąt": 90,
    "sto": 100, "dwiescie": 200, "dwieście": 200, "trzysta": 300, "czterysta": 400, "piecset": 500, "pięćset": 500,
    "szescset": 600, "sześćset": 600, "siedemset": 700, "osiemset": 800, "dziewiecset": 900, "dziewięćset": 900,
    "tysiac": 1000, "tysiąac": 1000, "tysiace": 1000, "tysiące": 1000,
}

def parse_pl_number(value: Any) -> float:
    """Parse numeric values or simple Polish text numbers used in service forms."""
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).lower().strip().replace(",", ".")
    try:
        return float(s)
    except ValueError:
        pass

    if "przecinek" in s:
        left, right = s.split("przecinek", 1)
        return float(int(parse_pl_number(left))) + float("0." + "".join(str(int(parse_pl_number(tok))) for tok in right.split() if tok))

    tokens = s.replace("-", " ").split()
    total = 0
    current = 0
    for tok in tokens:
        if tok in ("tysiac", "tysiąac", "tysiace", "tysiące"):
            total += max(1, current) * 1000
            current = 0
        elif tok in PL_NUMBER_WORDS:
            current += PL_NUMBER_WORDS[tok]
    return float(total + current)
