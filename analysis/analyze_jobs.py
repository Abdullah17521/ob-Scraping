import pandas as pd
from pathlib import Path
import re

def split_skills(skills):
    if pd.isna(skills):
        return []
    if isinstance(skills, list):
        return skills
    text = str(skills)
    tokens = re.split(r",|;|\\n|\\|\\/", text)
    return [t.strip() for t in tokens if t.strip()]


def main():
    data_path = Path("data") / "final" / "jobs.csv"
    if not data_path.exists():
        print(f"Missing {data_path}. Run scrapy spider first.")
        return

    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} job rows")

    skills_series = pd.Series([skill for row in df["required_skills"].fillna("").apply(split_skills) for skill in row])
    top_skills = skills_series.value_counts().head(5)

    top_cities = df["location"].fillna("Unknown").value_counts().head(5)
    top_company = df["company_name"].fillna("Unknown").value_counts().head(1)

    role_type = df["employment_type"].fillna("Unknown").str.lower()
    internship_count = role_type.str.contains("intern").sum()
    fulltime_count = role_type.str.contains("full") | role_type.str.contains("full-time")
    fulltime_count = fulltime_count.sum()
    total = len(df)

    out = Path("analysis") / "insights.txt"
    with open(out, "w", encoding="utf-8") as f:
        f.write("Job Scraping and Analysis Insights\n")
        f.write("===============================\n")
        f.write(f"Total records: {total}\n")
        f.write("\nTop 5 most demanded skills:\n")
        for skill, count in top_skills.items():
            f.write(f"- {skill}: {count}\n")
        f.write("\nTop locations/cities with most openings:\n")
        for loc, count in top_cities.items():
            f.write(f"- {loc}: {count}\n")
        f.write("\nCompany with most active hiring:\n")
        if not top_company.empty:
            c, ccount = top_company.index[0], top_company.iloc[0]
            f.write(f"- {c}: {ccount}\n")
        f.write("\nInternship vs Full-time roles:\n")
        f.write(f"- Internship count: {internship_count}\n")
        f.write(f"- Full-time count: {fulltime_count}\n")
        f.write(f"- Internship percentage: {internship_count / total * 100:.2f}%\n")
        f.write(f"- Full-time percentage: {fulltime_count / total * 100:.2f}%\n")

    print(f"Insights saved to {out}")


if __name__ == '__main__':
    main()
