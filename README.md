# Century of War

Interactive timeline visualization of 1,000+ military conflicts from 1900 to present day.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.0+-red)
![License](https://img.shields.io/badge/License-MIT-green)

## Overview

Century of War scrapes Wikipedia's "List of wars" articles and renders them as an interactive Gantt chart. Explore global conflict patterns across the 20th and 21st centuries with filtering by region, time period, duration, and name.

## Features

- **1,000+ conflicts** automatically scraped from Wikipedia (4 list pages covering 1900-present)
- **Interactive Gantt timeline** powered by Plotly — click any bar to open its Wikipedia article
- **Region classification** — Europe, Middle East, Asia, Africa, Americas, Pacific, Global (200+ keyword patterns)
- **Sidebar filters** — year range, region, minimum duration, text search
- **Analytics dashboard** — total conflicts, average duration, top region, longest war
- **Decade distribution** — stacked bar chart showing conflict trends by region
- **CSV export** — download filtered results

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app will open in your browser. On first launch it scrapes Wikipedia and caches the data in `wars.csv`. Click the refresh button to re-scrape.

## How It Works

| Module | Role |
|---|---|
| `fetch_wars.py` | Scrapes 4 Wikipedia "List of wars" pages using a 4-tier fallback parsing strategy |
| `wars_gantt.py` | Renders the interactive Gantt chart with filters, metrics, and decade distribution |
| `app.py` | Streamlit entry point — ties scraping and visualization together |

### Scraping Strategy

Wikipedia tables are inconsistent. The scraper tries 4 strategies in order:

1. **Separate columns** — explicit `Start` and `End` columns
2. **Combined date** — single `Date` column with year range (e.g. "1950-1953")
3. **Cell scan** — no standard columns found, scan all cells for year patterns
4. **Name extraction** — extract year from the conflict name itself

## Dataset

The generated `wars.csv` contains ~1,083 conflicts:

| Column | Description |
|---|---|
| `name` | Conflict name |
| `start_year` | Start year (1900-2026) |
| `end_year` | End year (ongoing conflicts use 2026) |
| `wiki_url` | Link to Wikipedia article |

## Running Tests

```bash
pip install pytest
python -m pytest -v
```

124 tests covering text cleaning, year extraction, all 4 scraping strategies, region detection (including previously misclassified conflicts), data loading, and configuration consistency.

## Tech Stack

- [Streamlit](https://streamlit.io/) — web UI framework
- [Plotly](https://plotly.com/python/) — interactive charts
- [Pandas](https://pandas.pydata.org/) — data processing
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) — Wikipedia HTML parsing

## HuggingFace

This project can be deployed as a [HuggingFace Space](https://huggingface.co/spaces) (Streamlit SDK). The dataset (`wars.csv`) can also be published separately as an HF Dataset for use in NLP, historical analysis, or conflict research.

## License

MIT
