"""Render a static, multi-chart HTML dashboard for GitHub Pages."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.io as pio

CSV = Path("data/jobs_clean.csv")
OUT = Path("docs/index.html")
OUT.parent.mkdir(parents=True, exist_ok=True)

pio.templates.default = "plotly_white"


def fig_html(fig, full=False) -> str:
    return pio.to_html(fig, include_plotlyjs="cdn" if full else False, full_html=False)


def main() -> None:
    if not CSV.exists():
        raise SystemExit(f"Missing {CSV}. Run preprocess.py first.")

    df = pd.read_csv(CSV)
    df["created"] = pd.to_datetime(df["created"], errors="coerce", utc=True)

    n_total = len(df)
    n_countries = df["country"].nunique()
    n_companies = df["company"].nunique()
    median_sal = df["salary_avg_usd"].median()

    # 1. Top skills
    skills = Counter()
    for s in df["skills"].dropna():
        skills.update(s.split("|"))
    skills.pop("", None)
    top_skills = pd.DataFrame(skills.most_common(20), columns=["skill", "count"])
    fig_skills = px.bar(
        top_skills.sort_values("count"), x="count", y="skill", orientation="h",
        title="Top 20 Skills Mentioned", color="count", color_continuous_scale="Viridis",
    )
    fig_skills.update_layout(showlegend=False, coloraxis_showscale=False, height=550)

    # 2. Salary distribution
    sal = df[df["salary_avg_usd"].between(5_000, 500_000)]
    fig_sal = px.histogram(
        sal, x="salary_avg_usd", nbins=50,
        title=f"Salary Distribution (USD, n={len(sal):,})",
        labels={"salary_avg_usd": "Average Salary (USD)"},
    )
    fig_sal.update_layout(height=420)

    # 3. Postings by country
    by_country = df["country"].value_counts().reset_index()
    by_country.columns = ["country", "postings"]
    fig_country = px.choropleth(
        by_country, locations="country", locationmode="ISO-3",
        color="postings", color_continuous_scale="Plasma",
        title="Postings by Country",
    )
    # Adzuna gives 2-letter codes; plotly needs 3-letter. Use country names instead.
    fig_country = px.bar(
        by_country.sort_values("postings"), x="postings", y="country", orientation="h",
        title="Postings by Country", color="postings", color_continuous_scale="Plasma",
    )
    fig_country.update_layout(showlegend=False, coloraxis_showscale=False, height=550)

    # 4. Role breakdown
    by_role = df["role"].value_counts().reset_index()
    by_role.columns = ["role", "count"]
    fig_role = px.pie(by_role, values="count", names="role", title="Role Breakdown", hole=0.4)
    fig_role.update_layout(height=450)

    # 5. Time trend
    trend = df.dropna(subset=["created"]).copy()
    trend["week"] = trend["created"].dt.to_period("W").dt.start_time
    weekly = trend.groupby(["week", "role"]).size().reset_index(name="count")
    fig_trend = px.line(
        weekly, x="week", y="count", color="role",
        title="Weekly Postings Over Time by Role",
    )
    fig_trend.update_layout(height=450)

    # 6. Contract type
    ct = df["contract_time"].fillna("unspecified").value_counts().reset_index()
    ct.columns = ["contract_time", "count"]
    fig_contract = px.bar(
        ct, x="contract_time", y="count", title="Full-time vs Part-time", color="contract_time",
    )
    fig_contract.update_layout(showlegend=False, height=380)

    # 7. Top employers
    top_emp = df["company"].value_counts().head(20).reset_index()
    top_emp.columns = ["company", "postings"]
    fig_emp = px.bar(
        top_emp.sort_values("postings"), x="postings", y="company", orientation="h",
        title="Top 20 Hiring Companies", color="postings", color_continuous_scale="Teal",
    )
    fig_emp.update_layout(showlegend=False, coloraxis_showscale=False, height=550)

    # 8. Median salary by role
    sal_role = (
        df[df["salary_avg_usd"].between(5_000, 500_000)]
        .groupby("role")["salary_avg_usd"].median().sort_values().reset_index()
    )
    fig_sal_role = px.bar(
        sal_role, x="salary_avg_usd", y="role", orientation="h",
        title="Median Salary by Role (USD)", color="salary_avg_usd",
        color_continuous_scale="Sunset",
    )
    fig_sal_role.update_layout(showlegend=False, coloraxis_showscale=False, height=420)

    median_sal_str = f"${median_sal:,.0f}" if pd.notna(median_sal) else "n/a"
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Global Data Science & IT Jobs Dashboard</title>
<style>
  body {{ font-family: -apple-system, system-ui, sans-serif; margin: 0; background: #f7f8fa; color: #1f2937; }}
  header {{ background: linear-gradient(135deg, #4f46e5, #7c3aed); color: white; padding: 36px 24px; }}
  header h1 {{ margin: 0 0 6px; font-size: 28px; }}
  header p {{ margin: 0; opacity: 0.9; }}
  .kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; padding: 20px 24px; }}
  .kpi {{ background: white; border-radius: 10px; padding: 18px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }}
  .kpi .v {{ font-size: 26px; font-weight: 700; color: #4f46e5; }}
  .kpi .l {{ font-size: 13px; color: #6b7280; margin-top: 4px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(520px, 1fr)); gap: 16px; padding: 0 24px 32px; }}
  .card {{ background: white; border-radius: 10px; padding: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }}
  footer {{ text-align: center; padding: 24px; color: #6b7280; font-size: 13px; }}
</style>
</head>
<body>
<header>
  <h1>Global Data Science &amp; IT Jobs Dashboard</h1>
  <p>Aggregated from the Adzuna API across 19 countries</p>
</header>
<section class="kpis">
  <div class="kpi"><div class="v">{n_total:,}</div><div class="l">Job postings</div></div>
  <div class="kpi"><div class="v">{n_countries}</div><div class="l">Countries</div></div>
  <div class="kpi"><div class="v">{n_companies:,}</div><div class="l">Unique employers</div></div>
  <div class="kpi"><div class="v">{median_sal_str}</div><div class="l">Median salary (USD)</div></div>
</section>
<section class="grid">
  <div class="card">{fig_html(fig_skills, full=True)}</div>
  <div class="card">{fig_html(fig_role)}</div>
  <div class="card">{fig_html(fig_sal)}</div>
  <div class="card">{fig_html(fig_sal_role)}</div>
  <div class="card">{fig_html(fig_country)}</div>
  <div class="card">{fig_html(fig_emp)}</div>
  <div class="card">{fig_html(fig_trend)}</div>
  <div class="card">{fig_html(fig_contract)}</div>
</section>
<footer>Data source: Adzuna API · Built with Plotly · Static site, hostable on GitHub Pages</footer>
</body>
</html>
"""
    OUT.write_text(html, encoding="utf-8")
    print(f"Dashboard → {OUT}  ({n_total:,} postings)")


if __name__ == "__main__":
    main()
