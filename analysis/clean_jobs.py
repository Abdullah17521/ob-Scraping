import pandas as pd
from pathlib import Path


def normalize_text(v):
    if pd.isna(v):
        return ""
    return str(v).strip()


def main():
    input_path = Path("data") / "final" / "jobs.csv"
    output_path = Path("data") / "final" / "jobs_clean_final.csv"
    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        return

    df = pd.read_csv(input_path)

    df["job_title"] = df["job_title"].apply(normalize_text)
    df["company_name"] = df["company_name"].apply(normalize_text)
    df["location"] = df["location"].apply(normalize_text)
    df["department"] = df["department"].apply(normalize_text)
    df["employment_type"] = df["employment_type"].apply(normalize_text)
    df["posted_date"] = df["posted_date"].apply(normalize_text)
    df["required_skills"] = df["required_skills"].apply(normalize_text)
    df["experience_level"] = df["experience_level"].apply(normalize_text)
    df["salary"] = df["salary"].apply(normalize_text)
    df["job_description"] = df["job_description"].apply(normalize_text)

    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"Saved cleaned jobs to {output_path} (rows={len(df)})")


if __name__ == "__main__":
    main()
