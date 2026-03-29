"""
fetch_wars.py
=============
Scrapes Wikipedia list-of-wars pages (1900-present) and writes wars.csv.
Wikipedia tables have SEPARATE "Start" and "End" columns — handled explicitly.

    python fetch_wars.py     # standalone
    from fetch_wars import run
"""

import re
import csv
import requests
from bs4 import BeautifulSoup, Tag

from config import HEADERS, BASE_URL, CURRENT_YEAR, CSV_FILE, LIST_PAGES


def _clean(cell: Tag) -> str:
    """Extract visible text from a cell, stripping hidden sort-key spans and citations."""
    for tag in cell.find_all(["span", "sup"],
                              style=lambda s: s and "display:none" in s):
        tag.decompose()
    for tag in cell.find_all(class_=["sortkey", "sort-key"]):
        tag.decompose()
    text = cell.get_text(" ", strip=True)
    text = re.sub(r'\[\d+\]', '', text)
    return text.strip()


def _first_year(text: str) -> int | None:
    m = re.search(r'\b(19\d{2}|20[012]\d)\b', text)
    return int(m.group(1)) if m else None


def _all_years(text: str) -> list[int]:
    return [int(y) for y in re.findall(r'\b(19\d{2}|20[012]\d)\b', text)]


def _is_ongoing(text: str) -> bool:
    return bool(re.search(r'\b(present|ongoing|current)\b', text, re.I))


def _col_index(headers: list[str], keywords: list[str]) -> int | None:
    for i, h in enumerate(headers):
        if any(kw in h for kw in keywords):
            return i
    return None


def _scrape_page(path: str, log=print) -> list[dict]:
    url = BASE_URL + path
    log(f"  Fetching {url} ...")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception as exc:
        log(f"  ERROR: {exc}")
        return []

    soup   = BeautifulSoup(resp.text, "html.parser")
    tables = soup.find_all("table", class_=lambda c: c and "wikitable" in c)
    wars   = []

    for table in tables:
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue

        # Parse header — collect ALL header rows (some tables have 2 header rows)
        header_text = []
        for row in rows[:3]:
            ths = row.find_all(["th"])
            if ths:
                header_text = [th.get_text(" ", strip=True).lower() for th in ths]
                break

        log(f"    headers: {header_text[:8]}")

        # Wikipedia List-of-wars table columns:
        # Conflict | Start | End | Belligerents... | Result
        name_col  = _col_index(header_text, ["conflict", "war", "name"])
        start_col = _col_index(header_text, ["start"])
        end_col   = _col_index(header_text, ["end", "finish"])
        date_col  = _col_index(header_text, ["date", "period", "year"])

        if name_col is None:
            name_col = 0

        log(f"    col indices → name={name_col} start={start_col} end={end_col} date={date_col}")

        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            if not cells or len(cells) < 2:
                continue

            # ── Name ──────────────────────────────────────────────────────
            if name_col >= len(cells):
                continue
            name_cell = cells[name_col]
            link      = name_cell.find("a", href=True)
            name      = link.get_text(strip=True) if link else _clean(name_cell)
            name      = re.sub(r'\[\d+\]', '', name).strip()
            if not name or len(name) < 4:
                continue
            wiki_url = (BASE_URL + link["href"]) if link else ""

            # ── Strategy 1: separate Start + End columns ───────────────────
            start, end = None, None

            if start_col is not None and start_col < len(cells):
                start = _first_year(_clean(cells[start_col]))

            if end_col is not None and end_col < len(cells):
                t = _clean(cells[end_col])
                end = CURRENT_YEAR if _is_ongoing(t) else _first_year(t)

            # ── Strategy 2: combined date column ───────────────────────────
            if start is None and date_col is not None and date_col < len(cells):
                t      = _clean(cells[date_col])
                years  = _all_years(t)
                if years:
                    start = years[0]
                    end   = CURRENT_YEAR if _is_ongoing(t) else years[-1]

            # ── Strategy 3: scan every cell for years ─────────────────────
            if start is None:
                all_y   = []
                ongoing = False
                for cell in cells:
                    t = _clean(cell)
                    if _is_ongoing(t):
                        ongoing = True
                    all_y += _all_years(t)
                valid = sorted(set(y for y in all_y if 1900 <= y <= CURRENT_YEAR))
                if valid:
                    start = valid[0]
                    end   = CURRENT_YEAR if ongoing else valid[-1]

            # ── Strategy 4: year in the war name ──────────────────────────
            if start is None:
                start = _first_year(name)
                end   = start

            if start is None or start < 1900 or start > CURRENT_YEAR:
                continue
            if end is None or end < start:
                end = start
            end = min(end, CURRENT_YEAR)

            wars.append({
                "name":       name,
                "start_year": start,
                "end_year":   end,
                "wiki_url":   wiki_url,
            })

    return wars


def run(output_file: str = CSV_FILE, log=print) -> int:
    log("Scraping Wikipedia war lists...")
    all_wars: list[dict] = []
    seen:     set[str]   = set()

    for path in LIST_PAGES:
        for war in _scrape_page(path, log=log):
            key = war["name"].lower()
            if key not in seen:
                seen.add(key)
                all_wars.append(war)

    all_wars.sort(key=lambda w: (w["start_year"], w["end_year"]))

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["name", "start_year", "end_year", "wiki_url"]
        )
        writer.writeheader()
        writer.writerows(all_wars)

    known = {w["name"]: w for w in all_wars}
    for check in ["World War I", "World War II", "Korean War", "Vietnam War"]:
        if check in known:
            w   = known[check]
            dur = w["end_year"] - w["start_year"]
            log(f"  {'✓' if dur > 0 else '✗ BROKEN'} {check}: {w['start_year']}–{w['end_year']} ({dur} yrs)")
        else:
            log(f"  ? {check}: not found")

    broken = sum(1 for w in all_wars if w["end_year"] == w["start_year"])
    log(f"\nSaved {len(all_wars)} conflicts → {output_file}")
    log(f"Zero-duration entries: {broken}/{len(all_wars)}")
    return len(all_wars)


if __name__ == "__main__":
    run()
