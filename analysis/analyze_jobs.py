import pandas as pd
import re
from pathlib import Path


def parse_salary_numeric(value):
    if pd.isna(value):
        return None
    text = str(value)
    # find numeric salary values like $100,000 or 100000
    matches = re.findall(r"\$?([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)", text.replace("k", "000"))
    nums = []
    for m in matches:
        try:
            n = float(m.replace(",", ""))
            nums.append(n)
        except ValueError:
            continue
    if not nums:
        return None
    if len(nums) == 1:
        return nums[0]
    return sum(nums) / len(nums)


def normalize_skill_list(cell):
    if pd.isna(cell) or not str(cell).strip():
        return []
    parts = [p.strip() for p in re.split(r",|;|\n", str(cell)) if p.strip()]
    return parts


def main():
    data_path = Path("data") / "final" / "jobs_clean.csv"
    if not data_path.exists():
        print("jobs_clean.csv not found. Run the spider and cleanup first.")
        return

    df = pd.read_csv(data_path)

    # Average salary
    df["salary_num"] = df["salary"].apply(parse_salary_numeric)
    avg_salary = df["salary_num"].dropna().mean()

    # Top skills
    all_skills = []
    for entry in df["required_skills"].fillna(""):
        all_skills.extend(normalize_skill_list(entry))
    top_skills = pd.Series([s for s in all_skills if s]).value_counts().head(5)

    # Top locations for Software Engineer roles
    se = df[df["job_title"].fillna("").str.contains("software engineer", case=False, na=False)]
    top_locations_se = se["location"].fillna("Unknown").value_counts().head(3)

    out_path = Path("analysis") / "insights.txt"
    salary_out = f"{avg_salary:.2f}" if not pd.isna(avg_salary) else "N/A"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("Data Science Web Scraping Insights\n")
        f.write("==============================\n")
        f.write(f"Total jobs analyzed: {len(df)}\n")
        f.write(f"Average numeric salary (USD-like normalized): {salary_out}\n")
        f.write("\nTop 5 demanded skills:\n")
        for skill, count in top_skills.items():
            f.write(f"- {skill}: {count}\n")
        f.write("\nTop 3 locations for Software Engineer roles:\n")
        if top_locations_se.empty:
            f.write("- None found for 'Software Engineer' role titles\n")
        else:
            for loc, count in top_locations_se.items():
                f.write(f"- {loc}: {count}\n")

    print(f"Insights written to {out_path}")


if __name__ == "__main__":
    main()
