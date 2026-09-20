"""
Math Term Normalization Layer for InklusifMath.

Normalizes spoken Indonesian mathematical phrases (from speech-to-text or user input)
into standard mathematical notations and symbols based on the official guidelines in
`docs/leksikon_matematika_baku.md`.

Examples:
    "satu per dua"                -> "1/2"
    "setengah"                    -> "1/2"
    "tiga per empat"              -> "3/4"
    "x kuadrat"                   -> "x²"
    "dua kuadrat"                 -> "2²"
    "dua pangkat tiga"            -> "2³"
    "akar kuadrat dari sembilan"  -> "√9"
    "akar dua"                    -> "√2"
    "dua x ditambah tiga sama dengan tujuh" -> "2x + 3 = 7"
    "buka kurung x ditambah satu tutup kurung" -> "(x + 1)"
"""

from __future__ import annotations

import re

# ── Spoken number word to digit mapping ───────────────────────────────────────

_NUMBER_WORDS: dict[str, int] = {
    "nol": 0,
    "satu": 1,
    "se": 1,
    "dua": 2,
    "tiga": 3,
    "empat": 4,
    "lima": 5,
    "enam": 6,
    "tujuh": 7,
    "delapan": 8,
    "sembilan": 9,
    "sepuluh": 10,
    "sebelas": 11,
    "dua belas": 12,
    "tiga belas": 13,
    "empat belas": 14,
    "lima belas": 15,
    "enam belas": 16,
    "tujuh belas": 17,
    "delapan belas": 18,
    "sembilan belas": 19,
    "dua puluh": 20,
    "tiga puluh": 30,
    "empat puluh": 40,
    "lima puluh": 50,
    "enam puluh": 60,
    "tujuh puluh": 70,
    "delapan puluh": 80,
    "sembilan puluh": 90,
    "seratus": 100,
}

# Number regex pattern (longest compound phrases FIRST so regex doesn't greedily cut words)
_NUM_WORD_PATTERN = (
    r"(?:(?:dua|tiga|empat|lima|enam|tujuh|delapan|sembilan)\s+puluh\s+(?:satu|dua|tiga|empat|lima|enam|tujuh|delapan|sembilan)|"
    r"(?:dua|tiga|empat|lima|enam|tujuh|delapan|sembilan)\s+belas|"
    r"(?:dua|tiga|empat|lima|enam|tujuh|delapan|sembilan)\s+puluh|"
    r"sebelas|sepuluh|seratus|"
    r"nol|satu|dua|tiga|empat|lima|enam|tujuh|delapan|sembilan|\d+)"
)


def _parse_number_word(word_str: str) -> str:
    """Convert a spoken number string (e.g. 'dua puluh lima', 'tiga', '12') into digits."""
    cleaned = word_str.strip().lower()
    if cleaned.isdigit():
        return cleaned

    # Check direct dictionary match
    if cleaned in _NUMBER_WORDS:
        return str(_NUMBER_WORDS[cleaned])

    # Compound numbers: e.g. 'dua puluh lima' -> 20 + 5 = 25
    parts = cleaned.split()
    if len(parts) == 3 and parts[1] == "puluh":
        tens = _NUMBER_WORDS.get(f"{parts[0]} puluh", 0)
        units = _NUMBER_WORDS.get(parts[2], 0)
        if tens and units:
            return str(tens + units)

    return word_str


# ── Superscript mapping ───────────────────────────────────────────────────────

_SUPERSCRIPT_DIGITS: dict[str, str] = {
    "0": "⁰",
    "1": "¹",
    "2": "²",
    "3": "³",
    "4": "⁴",
    "5": "⁵",
    "6": "⁶",
    "7": "⁷",
    "8": "⁸",
    "9": "⁹",
    "n": "ⁿ",
    "x": "ˣ",
    "y": "ʸ",
}

# ── Common Named Fractions ────────────────────────────────────────────────────

_NAMED_FRACTIONS: dict[str, str] = {
    "setengah": "1/2",
    "seperdua": "1/2",
    "sepertiga": "1/3",
    "seperempat": "1/4",
    "seperlima": "1/5",
    "seperenam": "1/6",
    "seperdelapan": "1/8",
    "sepersepuluh": "1/10",
}


def normalize_math_terms(text: str) -> str:
    """
    Normalize spoken Indonesian mathematical terms into standard symbols.

    Args:
        text: Input string (e.g., from Web Speech API or faster-whisper).

    Returns:
        Normalized string with mathematical symbols and expressions.
    """
    if not text or not text.strip():
        return text

    normalized = text

    # 1. Parentheses / Tanda Kurung
    # "buka kurung ... tutup kurung" -> "( ... )"
    normalized = re.sub(
        r"\bbuka\s+kurung\s+(.*?)\s+tutup\s+kurung\b",
        r"(\1)",
        normalized,
        flags=re.IGNORECASE,
    )
    normalized = re.sub(
        r"\bbuka\s+kurung\s+siku\s+(.*?)\s+tutup\s+kurung\s+siku\b",
        r"[\1]",
        normalized,
        flags=re.IGNORECASE,
    )
    normalized = re.sub(
        r"\bbuka\s+kurung\s+kurawal\s+(.*?)\s+tutup\s+kurung\s+kurawal\b",
        r"{\1}",
        normalized,
        flags=re.IGNORECASE,
    )

    # 2. Named Fractions (setengah, sepertiga, seperempat, dll)
    for name, frac in _NAMED_FRACTIONS.items():
        normalized = re.sub(rf"\b{name}\b", frac, normalized, flags=re.IGNORECASE)

    # 3. Explicit "pecahan dengan pembilang A dan penyebut B"
    def _replace_long_fraction(match: re.Match) -> str:
        numerator = _parse_number_word(match.group(1).strip())
        denominator = _parse_number_word(match.group(2).strip())
        return f"{numerator}/{denominator}"

    normalized = re.sub(
        r"\bpecahan\s+(?:dengan\s+)?pembilang\s+([a-zA-Z0-9\s]+?)\s+dan\s+penyebut\s+([a-zA-Z0-9\s]+?)(?=\s|$|,|\.)",
        _replace_long_fraction,
        normalized,
        flags=re.IGNORECASE,
    )

    # 4. Standard fractions: "(angka/variabel) per (angka/variabel)"
    # e.g., "satu per dua" -> "1/2", "3 per 4" -> "3/4", "dua per tiga" -> "2/3"
    def _replace_fraction(match: re.Match) -> str:
        num_raw = match.group(1).strip()
        denom_raw = match.group(2).strip()
        num = _parse_number_word(num_raw)
        denom = _parse_number_word(denom_raw)
        return f"{num}/{denom}"

    fraction_pattern = rf"\b({_NUM_WORD_PATTERN}|[a-zA-Z])\s+per\s+({_NUM_WORD_PATTERN}|[a-zA-Z])\b"
    normalized = re.sub(fraction_pattern, _replace_fraction, normalized, flags=re.IGNORECASE)

    # 5. Roots / Akar
    # "akar pangkat tiga dari X" -> "∛X"
    def _replace_cube_root(match: re.Match) -> str:
        radicand = _parse_number_word(match.group(1).strip())
        return f"∛{radicand}"

    normalized = re.sub(
        rf"\bakar\s+pangkat\s+(?:tiga|3)\s+dari\s+({_NUM_WORD_PATTERN}|[a-zA-Z]+|\([^)]+\))\b",
        _replace_cube_root,
        normalized,
        flags=re.IGNORECASE,
    )

    # "akar kuadrat dari X" / "akar dari X" / "akar X" -> "√X"
    def _replace_square_root(match: re.Match) -> str:
        radicand = _parse_number_word(match.group(1).strip())
        return f"√{radicand}"

    normalized = re.sub(
        rf"\bakar\s+(?:kuadrat\s+)?(?:dari\s+)?({_NUM_WORD_PATTERN}|[a-zA-Z]+|\([^)]+\))\b",
        _replace_square_root,
        normalized,
        flags=re.IGNORECASE,
    )

    # 6. Exponents / Pangkat
    # "X kuadrat" -> "X²"
    def _replace_kuadrat(match: re.Match) -> str:
        base = _parse_number_word(match.group(1).strip())
        return f"{base}²"

    normalized = re.sub(
        rf"\b({_NUM_WORD_PATTERN}|[a-zA-Z0-9\)]+)\s+kuadrat\b",
        _replace_kuadrat,
        normalized,
        flags=re.IGNORECASE,
    )

    # "X kubik" -> "X³"
    def _replace_kubik(match: re.Match) -> str:
        base = _parse_number_word(match.group(1).strip())
        return f"{base}³"

    normalized = re.sub(
        rf"\b({_NUM_WORD_PATTERN}|[a-zA-Z0-9\)]+)\s+kubik\b",
        _replace_kubik,
        normalized,
        flags=re.IGNORECASE,
    )

    # "X pangkat dua/tiga/.../N"
    def _replace_exponent(match: re.Match) -> str:
        base = _parse_number_word(match.group(1).strip())
        exp_raw = match.group(2).strip().lower()
        exp_val = _parse_number_word(exp_raw)

        if exp_val in ("2", "3"):
            return f"{base}{'²' if exp_val == '2' else '³'}"
        if exp_val.isdigit() and len(exp_val) == 1:
            return f"{base}{_SUPERSCRIPT_DIGITS.get(exp_val, '^' + exp_val)}"
        if exp_val in _SUPERSCRIPT_DIGITS:
            return f"{base}{_SUPERSCRIPT_DIGITS[exp_val]}"
        return f"{base}^{exp_val}"

    normalized = re.sub(
        rf"\b({_NUM_WORD_PATTERN}|[a-zA-Z0-9\)]+)\s+pangkat\s+({_NUM_WORD_PATTERN}|[a-zA-Z])\b",
        _replace_exponent,
        normalized,
        flags=re.IGNORECASE,
    )

    # 7. Comparison operators
    comparisons = [
        (r"\bkurang\s+dari\s+atau\s+sama\s+dengan\b", "≤"),
        (r"\blebih\s+kecil\s+(?:dari\s+)?atau\s+sama\s+dengan\b", "≤"),
        (r"\blebih\s+dari\s+atau\s+sama\s+dengan\b", "≥"),
        (r"\blebih\s+besar\s+(?:dari\s+)?atau\s+sama\s+dengan\b", "≥"),
        (r"\btidak\s+sama\s+dengan\b", "≠"),
        (r"\bkira-?kira\s+sama\s+dengan\b", "≈"),
        (r"\bhampir\s+sama\s+dengan\b", "≈"),
        (r"\bkurang\s+lebih\b", "±"),
        (r"\bplus\s+minus\b", "±"),
        (r"\bsama\s+dengan\b", "="),
        (r"\bkurang\s+dari\b", "<"),
        (r"\blebih\s+kecil\s+dari\b", "<"),
        (r"\blebih\s+dari\b", ">"),
        (r"\blebih\s+besar\s+dari\b", ">"),
    ]

    for pattern, sym in comparisons:
        normalized = re.sub(pattern, f" {sym} ", normalized, flags=re.IGNORECASE)

    # 8. Special constants & units
    constants = [
        (r"\b(?:phi|pi)\b", "π"),
        (r"\bderajat\b", "°"),
        (r"\bpersen\b", "%"),
        (r"\btak\s+(?:hingga|terhingga)\b", "∞"),
    ]
    for pattern, sym in constants:
        normalized = re.sub(pattern, sym, normalized, flags=re.IGNORECASE)

    # 9. Arithmetic operators between operands
    normalized = re.sub(r"\b(?:ditambah|tambah|plus)\b", " + ", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\b(?:dikurangi|kurang|minus)\b", " - ", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\b(?:dikali(?:kan)?|kali)\b", " × ", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\b(?:dibagi|bagi)\b", " ÷ ", normalized, flags=re.IGNORECASE)

    # 10. Normalizing variable coefficients (e.g., "dua x" -> "2x", "tiga y" -> "3y", "dua π r" -> "2πr")
    def _replace_variable_coeff(match: re.Match) -> str:
        num = _parse_number_word(match.group(1))
        var = match.group(2)
        return f"{num}{var}"

    normalized = re.sub(
        rf"\b({_NUM_WORD_PATTERN})\s*([a-zA-Zπ])(?![a-zA-Z])",
        _replace_variable_coeff,
        normalized,
        flags=re.IGNORECASE,
    )

    # Clean space between π and adjacent variable: "2π r" -> "2πr"
    normalized = re.sub(r"π\s+([a-zA-Z])\b", r"π\1", normalized)

    # 11. Normalize remaining standalone number words adjacent to math symbols
    # Words AFTER symbols: e.g. "+ tiga" -> "+ 3"
    def _replace_numbers_after_symbols(match: re.Match) -> str:
        sym = match.group(1)
        space = match.group(2)
        word = match.group(3)
        return f"{sym}{space}{_parse_number_word(word)}"

    normalized = re.sub(
        rf"([+\-×÷=≤≥<>≈≠(])(\s+)({_NUM_WORD_PATTERN})\b",
        _replace_numbers_after_symbols,
        normalized,
        flags=re.IGNORECASE,
    )

    # Words BEFORE symbols: e.g. "dua +" -> "2 +"
    def _replace_numbers_before_symbols(match: re.Match) -> str:
        word = match.group(1)
        space = match.group(2)
        sym = match.group(3)
        return f"{_parse_number_word(word)}{space}{sym}"

    normalized = re.sub(
        rf"\b({_NUM_WORD_PATTERN})(\s+)([+\-×÷=≤≥<>≈≠)])",
        _replace_numbers_before_symbols,
        normalized,
        flags=re.IGNORECASE,
    )

    # 12. Normalizing numbers before units: "sembilan puluh °" -> "90°", "seratus %" -> "100%"
    def _replace_numbers_before_units(match: re.Match) -> str:
        word = match.group(1)
        unit = match.group(2)
        return f"{_parse_number_word(word)}{unit}"

    normalized = re.sub(
        rf"\b({_NUM_WORD_PATTERN})\s*([°%])",
        _replace_numbers_before_units,
        normalized,
        flags=re.IGNORECASE,
    )

    # 13. Clean up excess whitespace
    normalized = re.sub(r"\s+", " ", normalized).strip()

    # Clean spaces around parentheses: "( x + 1 )" -> "(x + 1)"
    normalized = re.sub(r"\(\s+", "(", normalized)
    normalized = re.sub(r"\s+\)", ")", normalized)

    return normalized
