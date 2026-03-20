import pandas as pd
from pathlib import Path


def main():
    input_path = Path("data") / "final" / "jobs.csv"
    output_path = Path("data") / "final" / "jobs_filtered.csv"
    if not input_path.exists():
        print(f"Missing input file: {input_path}")
        return

    df = pd.read_csv(input_path)
    print(f"Loaded {len(df)} rows from {input_path}")

    # deduplicate by job_url and job_title/department fallback
    dedup = df.drop_duplicates(subset=["job_url"], keep="first")
    print(f"After dedup by job_url: {len(dedup)} rows")

    # filter out broad placeholder pages and unknown skills
    mask = (
        dedup["job_title"].fillna("").str.lower().map(lambda t: "unknown" not in t)
        & dedup["required_skills"].fillna("").str.lower().map(lambda s: len(s.strip()) > 0)
        & (dedup["required_skills"].fillna("").str.lower() != "unknown")
    )
    filtered = dedup[mask].copy()
    print(f"After filtering unknown or empty skills: {len(filtered)} rows")

    filtered.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"Saved filtered jobs to {output_path}")


if __name__ == "__main__":
    main()
