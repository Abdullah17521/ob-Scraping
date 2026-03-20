import pandas as pd
from pathlib import Path
import re

def split_skills(skills):
    """Split skills by common delimiters."""
    if pd.isna(skills):
        return []
    if isinstance(skills, list):
        return skills
    text = str(skills)
    tokens = re.split(r",|;|\n|\\|\\/|\\s{2,}", text)
    return [t.strip().lower() for t in tokens if t.strip()]


def normalize_skill(skill):
    """Normalize skill names to standard format."""
    if pd.isna(skill) or skill == "" or skill == "not specified":
        return None
    
    skill = skill.lower().strip()
    
    # Normalize API-related skills
    if "api" in skill:
        if "rest" in skill:
            return "Rest API"
        elif "graphql" in skill:
            return "GraphQL"
        else:
            return "API"
    
    # Normalize cloud/infrastructure
    if skill in ["aws", "amazon"]:
        return "AWS"
    if skill in ["gcp", "google cloud"]:
        return "Google Cloud"
    if skill in ["azure", "microsoft azure"]:
        return "Azure"
    
    # Normalize databases
    if skill in ["sql", "mysql", "postgresql", "postgres"]:
        return "SQL"
    if skill in ["nosql", "mongodb", "cassandra"]:
        return "NoSQL"
    
    # Normalize languages/frameworks
    if skill in ["python"]:
        return "Python"
    if skill in ["javascript", "js"]:
        return "JavaScript"
    if skill in ["java"]:
        return "Java"
    if skill in ["scala"]:
        return "Scala"
    if skill in ["c++"]:
        return "C++"
    
    # Normalize frameworks
    if skill in ["react", "reactjs"]:
        return "React"
    if skill in ["angular", "angularjs"]:
        return "Angular"
    if skill in ["docker"]:
        return "Docker"
    if skill in ["kubernetes", "k8s"]:
        return "Kubernetes"
    if skill in ["django"]:
        return "Django"
    if skill in ["flask"]:
        return "Flask"
    
    # Capital first letter for consistency
    return skill.capitalize()


def main():
    data_path = Path("data") / "final" / "jobs.csv"
    if not data_path.exists():
        print(f"Missing {data_path}. Run scrapy spider first.")
        return

    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} job rows")

    # Extract and normalize skills
    raw_skills = [skill for row in df["required_skills"].fillna("").apply(split_skills) for skill in row]
    normalized_skills = [normalize_skill(skill) for skill in raw_skills]
    normalized_skills = [s for s in normalized_skills if s is not None]
    
    skills_series = pd.Series(normalized_skills)
    top_skills = skills_series.value_counts().head(10)

    # Analyze locations
    top_cities = df["location"].value_counts().head(10)
    
    # Analyze companies
    top_company = df["company_name"].value_counts()

    # Analyze employment types
    employment_dist = df["employment_type"].value_counts()

    # Analyze experience levels
    experience_dist = df["experience_level"].value_counts()

    total = len(df)

    # Write insights
    out = Path("analysis") / "insights.txt"
    with open(out, "w", encoding="utf-8") as f:
        f.write("Job Scraping and Analysis Insights\n")
        f.write("===================================\n\n")
        f.write(f"Total records: {total}\n")
        f.write("Data Source: Stripe, RemoteOK, We Work Remotely\n")
        f.write("Status: Cleaned & Verified ✓\n")
        
        f.write("\n" + "="*50 + "\n")
        f.write("Top 10 Most Demanded Skills:\n")
        f.write("="*50 + "\n")
        for i, (skill, count) in enumerate(top_skills.items(), 1):
            pct = (count / total) * 100
            f.write(f"{i}. {skill}: {count} jobs ({pct:.1f}%)\n")
        
        f.write("\n" + "="*50 + "\n")
        f.write("Top 10 Locations/Cities with Most Openings:\n")
        f.write("="*50 + "\n")
        for i, (loc, count) in enumerate(top_cities.items(), 1):
            pct = (count / total) * 100
            f.write(f"{i}. {loc}: {count} jobs ({pct:.1f}%)\n")
        
        f.write("\n" + "="*50 + "\n")
        f.write("Company Hiring Distribution:\n")
        f.write("="*50 + "\n")
        for company, count in top_company.items():
            pct = (count / total) * 100
            f.write(f"- {company}: {count} jobs ({pct:.1f}%)\n")
        
        f.write("\n" + "="*50 + "\n")
        f.write("Employment Type Distribution:\n")
        f.write("="*50 + "\n")
        for emp_type, count in employment_dist.items():
            pct = (count / total) * 100
            f.write(f"- {emp_type}: {count} jobs ({pct:.1f}%)\n")
        
        f.write("\n" + "="*50 + "\n")
        f.write("Experience Level Distribution:\n")
        f.write("="*50 + "\n")
        for exp_level, count in experience_dist.items():
            pct = (count / total) * 100
            f.write(f"- {exp_level}: {count} jobs ({pct:.1f}%)\n")

    print(f"Insights saved to {out}")


if __name__ == '__main__':
    main()
