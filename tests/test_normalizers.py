"""Tests for normalizers.py"""
import pandas as pd
import pytest
from src.transform.normalizers import normalize_brand, normalize_brand_series, normalize_sales_bucket


class TestNormalizeBrand:
    def test_known_brand_lowercase(self):
        assert normalize_brand("Dell Inspiron 15") == "Dell"

    def test_hp_uppercase(self):
        assert normalize_brand("HP Pavilion 14 i5") == "HP"

    def test_lg_uppercase(self):
        assert normalize_brand("LG Gram 17") == "LG"

    def test_msi_uppercase(self):
        assert normalize_brand("MSI GF63") == "MSI"

    def test_alias_galaxy_book_to_samsung(self):
        assert normalize_brand("Samsung Galaxy Book 4") == "Samsung"

    def test_alias_macbook_to_apple(self):
        assert normalize_brand("MacBook Pro 14") == "Apple"

    def test_alias_legion_to_lenovo(self):
        assert normalize_brand("Lenovo Legion 5") == "Lenovo"

    def test_alias_rog_to_asus(self):
        assert normalize_brand("ASUS ROG Strix G15") == "Asus"

    def test_unknown_brand_returns_none(self):
        assert normalize_brand("Notebook Generic Brand X") is None

    def test_none_input(self):
        assert normalize_brand(None) is None

    def test_empty_string(self):
        assert normalize_brand("") is None


class TestNormalizeBrandSeries:
    def test_series(self):
        series = pd.Series(["Dell XPS 13", "MacBook Air", "Unknown Model", None])
        result = normalize_brand_series(series)
        assert result[0] == "Dell"
        assert result[1] == "Apple"
        assert result[2] is None
        assert result[3] is None


class TestNormalizeSalesBucket:
    def test_simple_number(self):
        count, bucket = normalize_sales_bucket(pd.Series(["150 vendidos"]))
        assert count[0] == pytest.approx(150.0)
        assert str(bucket[0]) == "100-500"

    def test_mil_multiplier(self):
        count, bucket = normalize_sales_bucket(pd.Series(["+2 mil vendidos"]))
        assert count[0] == pytest.approx(2000.0)
        assert str(bucket[0]) == "1k-5k"

    def test_em_sentinel(self):
        count, bucket = normalize_sales_bucket(pd.Series(["em estoque"]))
        assert count[0] == pytest.approx(0.0)

    def test_nan_input(self):
        count, _ = normalize_sales_bucket(pd.Series([None]))
        assert count[0] == pytest.approx(0.0)
