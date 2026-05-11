"""Clean, dedupe, normalize and enrich the raw Adzuna dump."""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path("data/raw/jobs_raw.json")
OUT = Path("data/jobs_clean.csv")
OUT.parent.mkdir(parents=True, exist_ok=True)

# Approximate USD conversion rates (rough, for visualization only)
FX_TO_USD = {
    "gb": 1.27, "us": 1.00, "au": 0.66, "at": 1.08, "be": 1.08, "br": 0.20,
    "ca": 0.73, "ch": 1.12, "de": 1.08, "es": 1.08, "fr": 1.08, "in": 0.012,
    "it": 1.08, "mx": 0.058, "nl": 1.08, "nz": 0.61, "pl": 0.25, "sg": 0.74,
    "za": 0.054,
}

SKILLS = [
    "python", "r", "sql", "java", "javascript", "typescript", "scala", "go", "rust", "c++", "c#",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "linux", "git",
    "spark", "hadoop", "kafka", "airflow", "snowflake", "databricks", "redshift", "bigquery",
    "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
    "tableau", "power bi", "looker", "excel",
    "nlp", "computer vision", "deep learning", "mlops",
    "django", "flask", "fastapi", "react", "node",
    "etl", "data warehouse", "data lake",
]

ROLE_BUCKETS = {
    "Data Scientist": ["data scientist"],
    "Data Analyst": ["data analyst", "business analyst", "bi analyst"],
    "Data Engineer": ["data engineer"],
    "ML Engineer": ["machine learning", "ml engineer", "ai engineer"],
    "Software Engineer": ["software engineer", "backend", "full stack", "fullstack", "frontend"],
    "DevOps / Cloud": ["devops", "cloud engineer", "site reliability", "sre", "platform engineer"],
    "BI / Analytics": ["business intelligence", "bi developer", "analytics engineer"],
}


def bucket_role(title: str) -> str:
    t = (title or "").lower()
    for label, keys in ROLE_BUCKETS.items():
        if any(k in t for k in keys):
            return label
    return "Other IT / Tech"


def extract_skills(text: str) -> list[str]:
    if not text:
        return []
    t = text.lower()
    found = []
    for s in SKILLS:
        pattern = r"(?<![a-z0-9])" + re.escape(s) + r"(?![a-z0-9])"
        if re.search(pattern, t):
            found.append(s)
    return found


def main() -> None:
    if not RAW.exists():
        raise SystemExit(f"Missing {RAW}. Run scraper.py first.")

    raw = json.loads(RAW.read_text())
    print(f"Loaded {len(raw):,} raw postings")

    rows = []
    for j in raw:
        country = j.get("_country", "")
        sal_min = j.get("salary_min")
        sal_max = j.get("salary_max")
        fx = FX_TO_USD.get(country, np.nan)
        rows.append({
            "id": j.get("id"),
            "title": j.get("title", "").strip(),
            "company": (j.get("company") or {}).get("display_name"),
            "location": (j.get("location") or {}).get("display_name"),
            "country": country.upper(),
            "category": (j.get("category") or {}).get("label"),
            "contract_type": j.get("contract_type"),
            "contract_time": j.get("contract_time"),
            "created": j.get("created"),
            "description": j.get("description", ""),
            "salary_min": sal_min,
            "salary_max": sal_max,
            "salary_avg_usd": (
                ((sal_min + sal_max) / 2 * fx) if sal_min and sal_max and not np.isnan(fx) else np.nan
            ),
            "url": j.get("redirect_url"),
            "query": j.get("_query"),
        })

    df = pd.DataFrame(rows)
    before = len(df)

    # Dedupe by id, then by (title, company, country)
    df = df.drop_duplicates(subset=["id"])
    df = df.drop_duplicates(subset=["title", "company", "country"])
    df = df[df["title"].notna() & (df["title"] != "")]

    df["created"] = pd.to_datetime(df["created"], errors="coerce", utc=True)
    df["posted_date"] = df["created"].dt.date
    df["posted_week"] = df["created"].dt.to_period("W").astype(str)

    df["role"] = df["title"].map(bucket_role)
    df["skills"] = df["description"].map(extract_skills)
    df["n_skills"] = df["skills"].map(len)

    # Drop the heavy description column from the final csv
    df_out = df.drop(columns=["description"])
    # Convert skills list to pipe-delimited string for CSV friendliness
    df_out["skills"] = df_out["skills"].map(lambda xs: "|".join(xs))

    df_out.to_csv(OUT, index=False)
    print(f"Cleaned: {before:,} → {len(df_out):,} rows")
    print(f"Saved → {OUT}")


if __name__ == "__main__":
    main()
