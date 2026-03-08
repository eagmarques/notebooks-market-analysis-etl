"""Tests for cleaners.py"""
import pandas as pd
import pytest
from src.transform.cleaners import clean_prices, clean_reviews


class TestCleanPrices:
    def test_brazilian_format(self):
        series = pd.Series(["1.234,56"])
        result = clean_prices(series)
        assert result[0] == pytest.approx(1234.56)

    def test_plain_integer_string(self):
        result = clean_prices(pd.Series(["2500"]))
        assert result[0] == pytest.approx(2500.0)

    def test_none_becomes_nan(self):
        result = clean_prices(pd.Series([None]))
        assert pd.isna(result[0])

    def test_non_numeric_becomes_nan(self):
        result = clean_prices(pd.Series(["abc"]))
        assert pd.isna(result[0])

    def test_multiple_values(self):
        series = pd.Series(["3.500,00", "2.999,99", None, "abc"])
        result = clean_prices(series)
        assert result[0] == pytest.approx(3500.0)
        assert result[1] == pytest.approx(2999.99)
        assert pd.isna(result[2])
        assert pd.isna(result[3])


class TestCleanReviews:
    def test_comma_decimal(self):
        result = clean_reviews(pd.Series(["4,8"]))
        assert result[0] == pytest.approx(4.8)

    def test_with_ou_suffix(self):
        result = clean_reviews(pd.Series(["4,8 ou"]))
        assert result[0] == pytest.approx(4.8)

    def test_none_becomes_nan(self):
        result = clean_reviews(pd.Series([None]))
        assert pd.isna(result[0])

    def test_already_float_string(self):
        result = clean_reviews(pd.Series(["4.5"]))
        assert result[0] == pytest.approx(4.5)
