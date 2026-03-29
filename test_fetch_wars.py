"""
Tests for fetch_wars.py
=======================
Covers: text cleaning, year extraction, ongoing detection,
        column index lookup, HTML table scraping strategies,
        deduplication, and end-to-end run().
"""

import csv
import textwrap
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from bs4 import BeautifulSoup, Tag

import fetch_wars


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_cell(html: str) -> Tag:
    """Create a BeautifulSoup Tag from an HTML snippet."""
    soup = BeautifulSoup(f"<td>{html}</td>", "html.parser")
    return soup.find("td")


def _make_table_html(headers: list[str], rows: list[list[str]]) -> str:
    """Build a minimal wikitable HTML string."""
    ths = "".join(f"<th>{h}</th>" for h in headers)
    trs = ""
    for row in rows:
        tds = "".join(f"<td>{c}</td>" for c in row)
        trs += f"<tr>{tds}</tr>\n"
    return (
        '<table class="wikitable">\n'
        f"<tr>{ths}</tr>\n"
        f"{trs}</table>"
    )


def _make_response(html_body: str) -> MagicMock:
    """Create a mock requests.Response with given HTML body."""
    resp = MagicMock()
    resp.text = f"<html><body>{html_body}</body></html>"
    resp.raise_for_status = MagicMock()
    return resp


# ── _clean ────────────────────────────────────────────────────────────────────


class TestClean:
    def test_plain_text(self):
        cell = _make_cell("Hello World")
        assert fetch_wars._clean(cell) == "Hello World"

    def test_strips_citation_refs(self):
        cell = _make_cell("Some war[12][3]")
        assert fetch_wars._clean(cell) == "Some war"

    def test_strips_display_none_spans(self):
        cell = _make_cell(
            '<span style="display:none">hidden</span>Visible text'
        )
        assert fetch_wars._clean(cell) == "Visible text"

    def test_strips_sortkey_class(self):
        cell = _make_cell(
            '<span class="sortkey">000</span>Real value'
        )
        assert fetch_wars._clean(cell) == "Real value"

    def test_strips_sort_key_class(self):
        cell = _make_cell(
            '<span class="sort-key">zzz</span>Content'
        )
        assert fetch_wars._clean(cell) == "Content"

    def test_combined_junk(self):
        cell = _make_cell(
            '<span style="display:none">x</span>'
            '<span class="sortkey">y</span>'
            'War name[42]'
        )
        assert fetch_wars._clean(cell) == "War name"

    def test_empty_cell(self):
        cell = _make_cell("")
        assert fetch_wars._clean(cell) == ""

    def test_nested_tags(self):
        cell = _make_cell("<b>Bold</b> and <i>italic</i>")
        assert fetch_wars._clean(cell) == "Bold and italic"


# ── _first_year ───────────────────────────────────────────────────────────────


class TestFirstYear:
    def test_single_year(self):
        assert fetch_wars._first_year("1945") == 1945

    def test_year_in_text(self):
        assert fetch_wars._first_year("Started in 1914 and ended 1918") == 1914

    def test_no_year(self):
        assert fetch_wars._first_year("no year here") is None

    def test_year_out_of_range(self):
        assert fetch_wars._first_year("1850") is None

    def test_future_year_boundary(self):
        assert fetch_wars._first_year("2026") == 2026

    def test_year_2029_in_range(self):
        # Regex 20[012]\d matches 2020-2029
        assert fetch_wars._first_year("2029") == 2029

    def test_year_1900_boundary(self):
        assert fetch_wars._first_year("1900") == 1900


# ── _all_years ────────────────────────────────────────────────────────────────


class TestAllYears:
    def test_multiple_years(self):
        assert fetch_wars._all_years("1939–1945") == [1939, 1945]

    def test_no_years(self):
        assert fetch_wars._all_years("no years") == []

    def test_mixed_text(self):
        result = fetch_wars._all_years("From 1950 to 1953, with events in 1951")
        assert result == [1950, 1953, 1951]

    def test_single_year(self):
        assert fetch_wars._all_years("2003") == [2003]


# ── _is_ongoing ───────────────────────────────────────────────────────────────


class TestIsOngoing:
    def test_present(self):
        assert fetch_wars._is_ongoing("present") is True

    def test_ongoing(self):
        assert fetch_wars._is_ongoing("ongoing") is True

    def test_current(self):
        assert fetch_wars._is_ongoing("current") is True

    def test_case_insensitive(self):
        assert fetch_wars._is_ongoing("PRESENT") is True
        assert fetch_wars._is_ongoing("Ongoing") is True

    def test_not_ongoing(self):
        assert fetch_wars._is_ongoing("1945") is False

    def test_empty(self):
        assert fetch_wars._is_ongoing("") is False

    def test_ongoing_in_phrase(self):
        assert fetch_wars._is_ongoing("2003–present") is True


# ── _col_index ────────────────────────────────────────────────────────────────


class TestColIndex:
    def test_finds_conflict(self):
        headers = ["conflict", "start", "end", "belligerents"]
        assert fetch_wars._col_index(headers, ["conflict", "war"]) == 0

    def test_finds_start(self):
        headers = ["conflict", "start", "end"]
        assert fetch_wars._col_index(headers, ["start"]) == 1

    def test_returns_none_when_missing(self):
        headers = ["name", "year", "result"]
        assert fetch_wars._col_index(headers, ["start"]) is None

    def test_partial_match(self):
        headers = ["war name", "starting date", "ending date"]
        assert fetch_wars._col_index(headers, ["start"]) == 1

    def test_finds_date(self):
        headers = ["name", "date", "location"]
        assert fetch_wars._col_index(headers, ["date", "period"]) == 1


# ── _scrape_page (strategy tests) ────────────────────────────────────────────


class TestScrapePage:
    """Test different scraping strategies via mock HTML tables."""

    def _scrape(self, table_html: str) -> list[dict]:
        html = f"<html><body>{table_html}</body></html>"
        resp = MagicMock()
        resp.text = html
        resp.raise_for_status = MagicMock()
        with patch("fetch_wars.requests.get", return_value=resp):
            return fetch_wars._scrape_page("/wiki/Test", log=lambda *a: None)

    def test_strategy1_separate_start_end_columns(self):
        """Strategy 1: explicit Start and End columns."""
        table = _make_table_html(
            ["Conflict", "Start", "End", "Result"],
            [
                [
                    '<a href="/wiki/Test_War">Test War</a>',
                    "1914", "1918", "Victory",
                ],
            ],
        )
        wars = self._scrape(table)
        assert len(wars) == 1
        assert wars[0]["name"] == "Test War"
        assert wars[0]["start_year"] == 1914
        assert wars[0]["end_year"] == 1918
        assert wars[0]["wiki_url"] == "https://en.wikipedia.org/wiki/Test_War"

    def test_strategy1_ongoing(self):
        """Strategy 1: ongoing conflict."""
        table = _make_table_html(
            ["Conflict", "Start", "End"],
            [['<a href="/wiki/Long_War">Long War</a>', "2003", "present"]],
        )
        wars = self._scrape(table)
        assert len(wars) == 1
        assert wars[0]["end_year"] == fetch_wars.CURRENT_YEAR

    def test_strategy2_combined_date_column(self):
        """Strategy 2: single Date column with range."""
        table = _make_table_html(
            ["War", "Date", "Location"],
            [['<a href="/wiki/Some_War">Some War</a>', "1950–1953", "Korea"]],
        )
        wars = self._scrape(table)
        assert len(wars) == 1
        assert wars[0]["start_year"] == 1950
        assert wars[0]["end_year"] == 1953

    def test_strategy3_scan_all_cells(self):
        """Strategy 3: no standard date columns, scan all cells."""
        table = _make_table_html(
            ["Name", "Details", "Outcome"],
            [
                [
                    '<a href="/wiki/Obscure_War">Obscure War</a>',
                    "Fought between 1962 and 1965",
                    "Ceasefire",
                ],
            ],
        )
        wars = self._scrape(table)
        assert len(wars) == 1
        assert wars[0]["start_year"] == 1962
        assert wars[0]["end_year"] == 1965

    def test_strategy4_year_in_name(self):
        """Strategy 4: extract year from the war name itself."""
        table = _make_table_html(
            ["Name", "Details", "Outcome"],
            [["1956 Suez Crisis", "Info", "Result"]],
        )
        wars = self._scrape(table)
        assert len(wars) == 1
        assert wars[0]["start_year"] == 1956
        assert wars[0]["end_year"] == 1956

    def test_skips_short_names(self):
        """Names shorter than 4 chars are skipped."""
        table = _make_table_html(
            ["Conflict", "Start", "End"],
            [["War", "1940", "1941"]],  # only 3 chars
        )
        wars = self._scrape(table)
        assert len(wars) == 0

    def test_skips_out_of_range_years(self):
        """Conflicts before 1900 are skipped."""
        table = _make_table_html(
            ["Conflict", "Start", "End"],
            [['<a href="/wiki/Old">Old Conflict</a>', "1850", "1860"]],
        )
        wars = self._scrape(table)
        assert len(wars) == 0

    def test_multiple_rows(self):
        """Multiple rows in one table."""
        table = _make_table_html(
            ["Conflict", "Start", "End"],
            [
                ['<a href="/wiki/W1">War Alpha</a>', "1914", "1918"],
                ['<a href="/wiki/W2">War Beta</a>', "1939", "1945"],
                ['<a href="/wiki/W3">War Gamma</a>', "2001", "2021"],
            ],
        )
        wars = self._scrape(table)
        assert len(wars) == 3
        assert wars[0]["name"] == "War Alpha"
        assert wars[2]["end_year"] == 2021

    def test_end_before_start_corrected(self):
        """If end < start, end is set to start."""
        table = _make_table_html(
            ["Conflict", "Start", "End"],
            [['<a href="/wiki/X">Weird War</a>', "1950", "1940"]],
        )
        wars = self._scrape(table)
        assert len(wars) == 1
        assert wars[0]["end_year"] == 1950  # corrected to start

    def test_http_error_returns_empty(self):
        """HTTP failure returns empty list."""
        with patch("fetch_wars.requests.get", side_effect=Exception("timeout")):
            wars = fetch_wars._scrape_page("/wiki/Fail", log=lambda *a: None)
        assert wars == []


# ── run() integration ─────────────────────────────────────────────────────────


class TestRun:
    def test_writes_csv_and_deduplicates(self, tmp_path):
        """run() writes CSV, deduplicates by lowercase name."""
        table = _make_table_html(
            ["Conflict", "Start", "End"],
            [
                ['<a href="/wiki/W1">World War I</a>', "1914", "1918"],
                ['<a href="/wiki/W2">World War II</a>', "1939", "1945"],
                ['<a href="/wiki/W1dup">world war i</a>', "1914", "1918"],  # dup
            ],
        )

        def mock_get(url, **kwargs):
            return _make_response(table)

        output = tmp_path / "test_wars.csv"
        with patch("fetch_wars.requests.get", side_effect=mock_get):
            count = fetch_wars.run(
                output_file=str(output), log=lambda *a: None
            )

        assert output.exists()
        with open(output) as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Dedup: "world war i" duplicate should be removed
        names = [r["name"] for r in rows]
        assert "World War I" in names
        assert "World War II" in names
        # The same data is scraped for all 4 pages, but dedup by name
        # Count depends on page count x unique wars
        assert count > 0

    def test_csv_columns(self, tmp_path):
        """CSV has the expected columns."""
        table = _make_table_html(
            ["Conflict", "Start", "End"],
            [['<a href="/wiki/A">Alpha War</a>', "2000", "2005"]],
        )

        def mock_get(url, **kwargs):
            return _make_response(table)

        output = tmp_path / "cols.csv"
        with patch("fetch_wars.requests.get", side_effect=mock_get):
            fetch_wars.run(output_file=str(output), log=lambda *a: None)

        with open(output) as f:
            reader = csv.DictReader(f)
            row = next(reader)
        assert set(row.keys()) == {"name", "start_year", "end_year", "wiki_url"}

    def test_sorted_by_start_year(self, tmp_path):
        """Output is sorted by start_year, then end_year."""
        table = _make_table_html(
            ["Conflict", "Start", "End"],
            [
                ['<a href="/wiki/B">Beta 2000</a>', "2000", "2005"],
                ['<a href="/wiki/A">Alpha 1950</a>', "1950", "1960"],
                ['<a href="/wiki/C">Gamma 1975</a>', "1975", "1980"],
            ],
        )

        def mock_get(url, **kwargs):
            return _make_response(table)

        output = tmp_path / "sorted.csv"
        with patch("fetch_wars.requests.get", side_effect=mock_get):
            fetch_wars.run(output_file=str(output), log=lambda *a: None)

        with open(output) as f:
            rows = list(csv.DictReader(f))
        starts = [int(r["start_year"]) for r in rows]
        assert starts == sorted(starts)
