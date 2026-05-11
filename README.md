# Global Data Science & IT Jobs Dashboard

Scrape, clean, and visualize ~5,000+ Data Science and IT job postings worldwide. The output is a static HTML dashboard that publishes to **GitHub Pages**.

> Originally aimed at `za.indeed.com`, but Indeed blocks scrapers behind Cloudflare. Switched to the **Adzuna API** (free), which covers 19 countries with structured data for title, company, location, salary, contract type, posting date, and description.

## Stack

| Stage | Tool |
|---|---|
| Source | [Adzuna Jobs API](https://developer.adzuna.com) |
| Preprocessing | pandas / numpy |
| Visualization | Plotly (static HTML) |
| Hosting | GitHub Pages (`/docs` folder) |

## Quick start

```bash
# 1. install deps
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. get free API credentials at https://developer.adzuna.com
cp .env.example .env
# edit .env and paste your ADZUNA_APP_ID and ADZUNA_APP_KEY

# 3. run the pipeline
python scraper.py          # → data/raw/jobs_raw.json
python preprocess.py       # → data/jobs_clean.csv
python build_dashboard.py  # → docs/index.html
```

Open `docs/index.html` in a browser to preview.

## Deploy to GitHub Pages

1. Push this repo to GitHub.
2. Repo **Settings → Pages**: set **Source = `main` branch / `/docs` folder**.
3. Your dashboard will be live at `https://<username>.github.io/<repo>/`.

The `docs/` folder is the only thing Pages serves — everything else (raw data, scripts) is ignored at hosting time but lives in the repo for reproducibility.

## What's in the dashboard

- **KPIs** — total postings, countries covered, unique employers, median salary
- **Top 20 skills** mentioned in descriptions (Python, SQL, AWS, …)
- **Role breakdown** — Data Scientist, ML Engineer, Data Engineer, Software Engineer, DevOps, …
- **Salary distribution** in USD
- **Median salary by role**
- **Postings by country**
- **Top 20 hiring companies**
- **Weekly posting trend** by role
- **Full-time vs part-time** split

## Project structure

```
.
├── scraper.py            # Adzuna client (19 countries × 10 queries × 4 pages)
├── preprocess.py         # dedupe + clean + role bucket + skill extraction
├── build_dashboard.py    # static Plotly HTML → docs/index.html
├── requirements.txt
├── .env.example
├── .gitignore
├── data/
│   ├── raw/jobs_raw.json # gitignored
│   └── jobs_clean.csv    # final cleaned dataset
└── docs/
    └── index.html        # the GitHub Pages site
```

## Methodology notes

- **Coverage.** 19 countries on Adzuna (US, UK, AU, CA, DE, FR, IN, NL, SG, ZA, …). 10 query terms spanning DS + IT (`data scientist`, `data engineer`, `ml engineer`, `software engineer`, `devops`, etc.).
- **Deduplication.** First by Adzuna `id`, then again by `(title, company, country)` to catch the same posting served under multiple queries.
- **Salary normalization.** Approximate USD conversion via a hardcoded FX table — fine for visualization, not for financial analysis. Postings without salary fields are kept but excluded from salary charts.
- **Skill extraction.** Regex word-boundary matches against a curated keyword list of ~50 tools and frameworks. Conservative — favors precision over recall.
- **Role bucketing.** Title-keyword rules mapped to 8 buckets; anything unmatched falls into "Other IT / Tech".

## Limitations

- Adzuna's free tier has rate limits; full pipeline takes ~10–20 minutes.
- Salary data is sparse and partly model-predicted by Adzuna (`salary_is_predicted` flag in raw JSON).
- Skill extraction can't catch every variant ("Pytorch" yes, "torch" no, to avoid false positives).
