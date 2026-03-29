"""
Tests for wars_gantt.py
=======================
Covers: region detection, data loading, filtering logic, edge cases.
Streamlit rendering is not tested (requires browser/server).
"""

import csv
import textwrap
from pathlib import Path

import pandas as pd
import pytest

import wars_gantt


# ── _guess_region ─────────────────────────────────────────────────────────────


class TestGuessRegion:
    """Verify keyword-based region classification."""

    # Europe
    @pytest.mark.parametrize("name,expected", [
        ("Yugoslav Wars", "Europe"),
        ("Russo-Ukrainian War", "Europe"),
        ("Greek Civil War", "Europe"),
        ("Polish–Soviet War", "Europe"),
        ("Franco-Prussian aftermath", "Europe"),
        ("Balkan Wars", "Europe"),
        ("Spanish Civil War", "Europe"),
        ("Troubles", "Europe"),
        ("Chechen War", "Europe"),
        ("Kosovo War", "Europe"),
        ("Croatian War of Independence", "Europe"),
    ])
    def test_europe(self, name, expected):
        assert wars_gantt._guess_region(name) == expected

    # Middle East
    @pytest.mark.parametrize("name,expected", [
        ("Iran–Iraq War", "Middle East"),
        ("Arab–Israeli conflict", "Middle East"),
        ("Gulf War", "Middle East"),
        ("Ottoman collapse", "Middle East"),
        ("Afghan Civil War", "Middle East"),
        ("Yemeni Civil War", "Middle East"),
        ("Syrian Civil War", "Middle East"),
        ("Turkish War of Independence", "Middle East"),
    ])
    def test_middle_east(self, name, expected):
        assert wars_gantt._guess_region(name) == expected

    # Asia
    @pytest.mark.parametrize("name,expected", [
        ("Korean War", "Asia"),
        ("Vietnam War", "Asia"),
        ("Sino-Japanese War", "Asia"),
        ("Indo-Pakistani War", "Asia"),
        ("Chinese Civil War", "Asia"),
        ("Cambodian–Vietnamese War", "Asia"),
        ("Indonesian National Revolution", "Asia"),
        ("Philippine–American War", "Asia"),
        ("Burma Campaign", "Asia"),
    ])
    def test_asia(self, name, expected):
        assert wars_gantt._guess_region(name) == expected

    # Africa
    @pytest.mark.parametrize("name,expected", [
        ("Rwandan Civil War", "Africa"),
        ("Angolan Civil War", "Africa"),
        ("Ethiopian Civil War", "Africa"),
        ("Congo Crisis", "Africa"),
        ("Nigerian Civil War", "Africa"),
        ("Liberian Civil War", "Africa"),
        ("Sierra Leone Civil War", "Africa"),
        ("Algerian War", "Africa"),
        ("Somali Civil War", "Africa"),
        ("Darfur conflict", "Africa"),
        ("Biafran War", "Africa"),
        ("Boko Haram insurgency", "Africa"),
        ("Rhodesian Bush War", "Africa"),
    ])
    def test_africa(self, name, expected):
        assert wars_gantt._guess_region(name) == expected

    # Americas
    @pytest.mark.parametrize("name,expected", [
        ("Colombian conflict", "Americas"),
        ("Cuban Revolution", "Americas"),
        ("Nicaraguan Revolution", "Americas"),
        ("Guatemalan Civil War", "Americas"),
        ("Haitian Revolution aftermath", "Americas"),
        ("American Civil Rights era", "Americas"),
        ("Mexican Revolution", "Americas"),
        ("Falklands War", "Americas"),
        ("FARC insurgency", "Americas"),
        ("Venezuelan crisis", "Americas"),
        ("Argentine dirty war", "Americas"),
    ])
    def test_americas(self, name, expected):
        assert wars_gantt._guess_region(name) == expected

    # Pacific
    @pytest.mark.parametrize("name,expected", [
        ("Pacific War", "Pacific"),
        ("Papua New Guinea conflict", "Pacific"),
    ])
    def test_pacific(self, name, expected):
        assert wars_gantt._guess_region(name) == expected

    # Global
    @pytest.mark.parametrize("name,expected", [
        ("World War I", "Global"),
        ("World War II", "Global"),
        ("Cold War", "Global"),
    ])
    def test_global(self, name, expected):
        assert wars_gantt._guess_region(name) == expected

    # Other (no keyword match)
    def test_unknown_defaults_to_other(self):
        assert wars_gantt._guess_region("Obscure Local Skirmish") == "Other"

    def test_case_insensitive(self):
        assert wars_gantt._guess_region("KOREAN WAR") == "Asia"
        assert wars_gantt._guess_region("gulf war") == "Middle East"

    # Document known misclassifications as baseline for future improvements
    @pytest.mark.parametrize("name,expected", [
        ("Boxer Rebellion", "Asia"),
        ("Mau Mau Uprising", "Africa"),
        ("Falklands War", "Americas"),
        ("Troubles", "Europe"),
        ("Somali Civil War", "Africa"),
        ("Mexican Revolution", "Americas"),
    ])
    def test_previously_misclassified_now_fixed(self, name, expected):
        """These were previously classified as 'Other', now correctly detected."""
        assert wars_gantt._guess_region(name) == expected


# ── load_data ─────────────────────────────────────────────────────────────────


@pytest.fixture
def sample_csv(tmp_path) -> Path:
    """Create a minimal wars.csv for testing."""
    csv_path = tmp_path / "wars.csv"
    rows = [
        {"name": "World War I", "start_year": 1914, "end_year": 1918, "wiki_url": "https://en.wikipedia.org/wiki/World_War_I"},
        {"name": "World War II", "start_year": 1939, "end_year": 1945, "wiki_url": "https://en.wikipedia.org/wiki/World_War_II"},
        {"name": "Korean War", "start_year": 1950, "end_year": 1953, "wiki_url": "https://en.wikipedia.org/wiki/Korean_War"},
        {"name": "Vietnam War", "start_year": 1955, "end_year": 1975, "wiki_url": "https://en.wikipedia.org/wiki/Vietnam_War"},
        {"name": "Gulf War", "start_year": 1990, "end_year": 1991, "wiki_url": ""},
        {"name": "Ongoing Conflict", "start_year": 2010, "end_year": 2026, "wiki_url": ""},
        {"name": "Zero Duration War", "start_year": 1956, "end_year": 1956, "wiki_url": ""},
    ]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "start_year", "end_year", "wiki_url"])
        writer.writeheader()
        writer.writerows(rows)
    return csv_path


class TestLoadData:
    def test_loads_correct_row_count(self, sample_csv):
        # Clear streamlit cache before testing
        wars_gantt.load_data.clear()
        df = wars_gantt.load_data(str(sample_csv))
        assert len(df) == 7

    def test_columns_present(self, sample_csv):
        wars_gantt.load_data.clear()
        df = wars_gantt.load_data(str(sample_csv))
        expected_cols = {"name", "start_year", "end_year", "duration", "region", "wiki_url", "display_end"}
        assert expected_cols.issubset(set(df.columns))

    def test_duration_calculated(self, sample_csv):
        wars_gantt.load_data.clear()
        df = wars_gantt.load_data(str(sample_csv))
        ww1 = df[df["name"] == "World War I"].iloc[0]
        assert ww1["duration"] == 4  # 1918 - 1914

    def test_zero_duration(self, sample_csv):
        wars_gantt.load_data.clear()
        df = wars_gantt.load_data(str(sample_csv))
        zd = df[df["name"] == "Zero Duration War"].iloc[0]
        assert zd["duration"] == 0

    def test_display_end_for_zero_duration(self, sample_csv):
        """Zero-duration wars get display_end = start_year + 1 for visibility."""
        wars_gantt.load_data.clear()
        df = wars_gantt.load_data(str(sample_csv))
        zd = df[df["name"] == "Zero Duration War"].iloc[0]
        assert zd["display_end"] == zd["start_year"] + 1

    def test_display_end_for_normal_duration(self, sample_csv):
        """Normal wars keep display_end == end_year."""
        wars_gantt.load_data.clear()
        df = wars_gantt.load_data(str(sample_csv))
        ww1 = df[df["name"] == "World War I"].iloc[0]
        assert ww1["display_end"] == ww1["end_year"]

    def test_region_assigned(self, sample_csv):
        wars_gantt.load_data.clear()
        df = wars_gantt.load_data(str(sample_csv))
        ww1 = df[df["name"] == "World War I"].iloc[0]
        assert ww1["region"] == "Global"

        korean = df[df["name"] == "Korean War"].iloc[0]
        assert korean["region"] == "Asia"

    def test_sorted_by_start_year(self, sample_csv):
        wars_gantt.load_data.clear()
        df = wars_gantt.load_data(str(sample_csv))
        starts = df["start_year"].tolist()
        assert starts == sorted(starts)

    def test_file_not_found_raises(self):
        wars_gantt.load_data.clear()
        with pytest.raises(FileNotFoundError):
            wars_gantt.load_data("/nonexistent/path.csv")

    def test_integer_types(self, sample_csv):
        wars_gantt.load_data.clear()
        df = wars_gantt.load_data(str(sample_csv))
        assert df["start_year"].dtype in ("int64", "int32")
        assert df["end_year"].dtype in ("int64", "int32")

    def test_filters_out_invalid_years(self, tmp_path):
        """Rows with start_year outside 1900–2026 are dropped."""
        csv_path = tmp_path / "bad.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "start_year", "end_year", "wiki_url"])
            writer.writeheader()
            writer.writerow({"name": "Too Old", "start_year": 1850, "end_year": 1860, "wiki_url": ""})
            writer.writerow({"name": "Too New", "start_year": 2030, "end_year": 2035, "wiki_url": ""})
            writer.writerow({"name": "Valid War", "start_year": 1950, "end_year": 1955, "wiki_url": ""})
        wars_gantt.load_data.clear()
        df = wars_gantt.load_data(str(csv_path))
        assert len(df) == 1
        assert df.iloc[0]["name"] == "Valid War"


# ── REGION_KEYWORDS / REGION_COLORS consistency ──────────────────────────────


class TestRegionConsistency:
    def test_all_keyword_regions_have_colors(self):
        """Every region in REGION_KEYWORDS has a corresponding color."""
        for region in wars_gantt.REGION_KEYWORDS:
            assert region in wars_gantt.REGION_COLORS, f"Missing color for {region}"

    def test_other_has_color(self):
        """The fallback 'Other' region has a color."""
        assert "Other" in wars_gantt.REGION_COLORS

    def test_no_empty_keyword_lists(self):
        """Every region has at least one keyword."""
        for region, kws in wars_gantt.REGION_KEYWORDS.items():
            assert len(kws) > 0, f"Empty keyword list for {region}"

    def test_keywords_are_lowercase(self):
        """All keywords should be lowercase for case-insensitive matching."""
        for region, kws in wars_gantt.REGION_KEYWORDS.items():
            for kw in kws:
                assert kw == kw.lower(), f"Keyword '{kw}' in {region} is not lowercase"
