"""Fetch Data Science + IT job postings worldwide from the Adzuna API."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")
BASE = "https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"

COUNTRIES = [
    "gb", "us", "au", "at", "be", "br", "ca", "ch", "de", "es",
    "fr", "in", "it", "mx", "nl", "nz", "pl", "sg", "za",
]

QUERIES = [
    "data scientist", "data analyst", "data engineer",
    "machine learning", "ai engineer", "business intelligence",
    "software engineer", "devops", "backend developer", "cloud engineer",
]

RESULTS_PER_PAGE = 50
MAX_PAGES_PER_QUERY = 4  # 19 countries * 10 queries * 4 pages * 50 = ~38k upper bound

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = Path("data/raw/jobs_raw.json")


def fetch(country: str, query: str, page: int) -> list[dict] | None:
    url = BASE.format(country=country, page=page)
    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "results_per_page": RESULTS_PER_PAGE,
        "what": query,
        "content-type": "application/json",
    }
    try:
        r = requests.get(url, params=params, timeout=20)
    except requests.RequestException as e:
        print(f"  network error {country}/{query}/p{page}: {e}")
        return None
    if r.status_code == 429:
        print("  rate limited — sleeping 30s")
        time.sleep(30)
        return fetch(country, query, page)
    if r.status_code != 200:
        return None
    return r.json().get("results", [])


def main() -> None:
    if not APP_ID or not APP_KEY:
        raise SystemExit("Missing ADZUNA_APP_ID / ADZUNA_APP_KEY — copy .env.example to .env and fill them in.")

    all_jobs: list[dict] = []
    seen_ids: set[str] = set()

    combos = [(c, q) for c in COUNTRIES for q in QUERIES]
    for country, query in tqdm(combos, desc="country/query"):
        for page in range(1, MAX_PAGES_PER_QUERY + 1):
            results = fetch(country, query, page)
            if not results:
                break
            new = 0
            for job in results:
                jid = str(job.get("id", ""))
                if jid and jid not in seen_ids:
                    seen_ids.add(jid)
                    job["_country"] = country
                    job["_query"] = query
                    all_jobs.append(job)
                    new += 1
            if new == 0:
                break
            time.sleep(0.25)  # be polite

    OUT_PATH.write_text(json.dumps(all_jobs, ensure_ascii=False))
    print(f"\nSaved {len(all_jobs):,} unique postings → {OUT_PATH}")


if __name__ == "__main__":
    main()
