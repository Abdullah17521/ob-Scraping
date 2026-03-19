import pandas as pd
import re
from pathlib import Path


def normalize_job_title(title):
    if pd.isna(title) or not str(title).strip():
        return "Unknown"
    return str(title).strip()


def normalize_company(row):
    source = row.get("company_name", "").strip()
    if source.startswith("http"):
        if "greenhouse.io" in source:
            return "Greenhouse Company"
        if "stripe.com" in row.get("job_url", ""):
            return "Stripe"
        return "Unknown"
    return source or "Unknown"


def normalize_location(v):
    if pd.isna(v) or not str(v).strip() or str(v).strip().lower() in ["unknown", ""]:
        return "Remote"
    return str(v).strip()


def normalize_employment_type(desc, title):
    txt = f"{desc} {title}".lower()
    if "intern" in txt:
        return "Internship"
    if "contract" in txt:
        return "Contract"
    if "part-time" in txt or "part time" in txt:
        return "Part-time"
    if "full-time" in txt or "full time" in txt:
        return "Full-time"
    return "Full-time"


def extract_skills(text):
    if pd.isna(text) or not str(text).strip():
        return "N/A"
    words = re.findall(r"(?:Python|SQL|AWS|Java|React|communication|analytics|data|sales|partner|marketing|technical)", text, flags=re.I)
    if words:
        return ", ".join(dict.fromkeys([w.strip().title() for w in words]))
    return "N/A"


def main():
    input_path = Path("data") / "final" / "jobs.csv"
    output_path = Path("data") / "final" / "jobs_clean.csv"
    df = pd.read_csv(input_path)

    out = pd.DataFrame()
    out["job_title"] = df["job_title"].fillna("Unknown").apply(normalize_job_title)
    out["company_name"] = df.apply(normalize_company, axis=1)
    out["location"] = df["location"].fillna("Remote").apply(normalize_location)
    out["department"] = df["department"].fillna("General").replace("", "General")
    out["employment_type"] = df.apply(lambda r: normalize_employment_type(r.get("job_description", ""), r.get("job_title", "")), axis=1)
    out["posted_date"] = df["posted_date"].fillna("Unknown").replace("", "Unknown")
    out["job_url"] = df["job_url"]
    out["job_description"] = df["job_description"].fillna("Not available").replace("", "Not available").apply(lambda t: re.sub(r"\s+", " ", str(t)).strip())
    out["required_skills"] = df["required_skills"].fillna("").apply(extract_skills)
    out["experience_level"] = df.get("experience_level", "").fillna("Not specified")
    out["salary"] = df.get("salary", "").fillna("Not specified")

    out.to_csv(output_path, index=False)
    print(f"Wrote cleaned job dataset to {output_path}")


if __name__ == "__main__":
    main()
