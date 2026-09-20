"""
Unit tests for Math Term Normalization Layer (app/services/math_normalizer.py).
"""

import pytest
from app.services.math_normalizer import normalize_math_terms


class TestFractionsNormalization:
    def test_named_fractions(self):
        assert normalize_math_terms("setengah") == "1/2"
        assert normalize_math_terms("seperdua") == "1/2"
        assert normalize_math_terms("sepertiga") == "1/3"
        assert normalize_math_terms("seperempat") == "1/4"

    def test_word_fractions(self):
        assert normalize_math_terms("satu per dua") == "1/2"
        assert normalize_math_terms("dua per tiga") == "2/3"
        assert normalize_math_terms("tiga per empat") == "3/4"
        assert normalize_math_terms("tujuh per delapan") == "7/8"

    def test_long_format_fraction(self):
        result = normalize_math_terms("pecahan dengan pembilang satu dan penyebut dua")
        assert "1/2" in result


class TestExponentsNormalization:
    def test_kuadrat_and_kubik(self):
        assert normalize_math_terms("x kuadrat") == "x²"
        assert normalize_math_terms("y kubik") == "y³"
        assert normalize_math_terms("dua kuadrat") == "2²"

    def test_pangkat_numbers(self):
        assert normalize_math_terms("x pangkat dua") == "x²"
        assert normalize_math_terms("a pangkat tiga") == "a³"
        assert normalize_math_terms("dua pangkat empat") == "2⁴"
        assert normalize_math_terms("x pangkat n") == "xⁿ"


class TestRootsNormalization:
    def test_square_roots(self):
        assert normalize_math_terms("akar dua") == "√2"
        assert normalize_math_terms("akar dari sembilan") == "√9"
        assert normalize_math_terms("akar kuadrat dari enam belas") == "√16"

    def test_cube_roots(self):
        assert normalize_math_terms("akar pangkat tiga dari delapan") == "∛8"
        assert normalize_math_terms("akar pangkat 3 dari dua puluh tujuh") == "∛27"


class TestOperatorsAndEquations:
    def test_basic_arithmetic(self):
        assert normalize_math_terms("dua ditambah tiga") == "2 + 3"
        assert normalize_math_terms("lima dikurangi dua") == "5 - 2"
        assert normalize_math_terms("tiga dikali empat") == "3 × 4"
        assert normalize_math_terms("sepuluh dibagi dua") == "10 ÷ 2"

    def test_comparisons(self):
        assert normalize_math_terms("x lebih besar dari lima") == "x > 5"
        assert normalize_math_terms("y kurang dari atau sama dengan sepuluh") == "y ≤ 10"
        assert normalize_math_terms("a tidak sama dengan b") == "a ≠ b"
        assert normalize_math_terms("pi kira-kira sama dengan 3,14") == "π ≈ 3,14"

    def test_parentheses(self):
        assert normalize_math_terms("buka kurung x ditambah satu tutup kurung") == "(x + 1)"

    def test_full_equation(self):
        result = normalize_math_terms("dua x ditambah tiga sama dengan tujuh")
        assert result == "2x + 3 = 7"

    def test_quadratic_equation(self):
        result = normalize_math_terms("x kuadrat dikurangi empat x ditambah empat sama dengan nol")
        assert result == "x² - 4x + 4 = 0"


class TestEdgeCasesAndNaturalSpeech:
    def test_empty_string(self):
        assert normalize_math_terms("") == ""
        assert normalize_math_terms("   ") == "   "

    def test_natural_speech_context(self):
        result = normalize_math_terms("Bagaimana cara menghitung satu per dua ditambah seperempat?")
        assert "1/2 + 1/4" in result

    def test_constants(self):
        assert normalize_math_terms("dua phi r") == "2πr"
        assert normalize_math_terms("sembilan puluh derajat") == "90°"
        assert normalize_math_terms("seratus persen") == "100%"
