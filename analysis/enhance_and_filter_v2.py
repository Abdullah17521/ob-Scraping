"""
Advanced job filtering and data cleaning for all sources.
Handles WWR enhancement, company name normalization, and comprehensive validation.
"""
import pandas as pd
import requests
import time
from bs4 import BeautifulSoup
from pathlib import Path
import re
import warnings

warnings.filterwarnings("ignore")


def normalize_company_name(name):
    """Normalize company names for consistency."""
    if pd.isna(name) or name == '':
        return 'Unknown'
    
    name = str(name).strip()
    
    # Normalize We Work Remotely variations
    if any(x in name.lower() for x in ['wework', 'remotely', 'wwr']):
        return 'We Work Remotely'
    
    # Normalize RemoteOK variations
    if 'remote' in name.lower() and 'ok' in name.lower():
        return 'RemoteOK'
    
    return name if name else 'Unknown'


def clean_location(loc):
    """Clean and standardize location field."""
    if pd.isna(loc) or loc == '':
        return 'Unknown'
    
    loc = str(loc).strip()
    
    # Remove RSS/feed artifacts
    if loc.endswith('.rss') or loc.endswith('.xml'):
        return 'Unknown'
    
    # Fix truncated location strings
    corrections = {
        'vestment Jobs': 'Investment Jobs',
        'Support jobs': 'Support',
        '🎧': '',
    }
    
    for old, new in corrections.items():
        if old in loc:
            loc = loc.replace(old, new).strip()
    
    return loc if loc else 'Unknown'


def clean_employment_type(emp_type):
    """Normalize employment type field."""
    if pd.isna(emp_type) or emp_type == '':
        return 'Not specified'
    
    emp_type = str(emp_type).strip()
    
    # Remove date strings that got mixed in
    if any(month in emp_type for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']):
        return 'Not specified'
    
    # Check if it looks like a date
    if any(x in emp_type for x in ['2026', '2025', 'UTC', '+0000']):
        return 'Not specified'
    
    valid_types = ['Intern', 'Full-time', 'Contract', 'Part-time', 'Freelance', 'Temporary']
    if emp_type in valid_types:
        return emp_type
    
    if emp_type.lower() == 'unknown':
        return 'Not specified'
    
    return 'Not specified' if not emp_type else emp_type


def clean_job_title(title):
    """Validate and clean job titles."""
    if pd.isna(title) or title == '':
        return None
    
    title = str(title).strip()
    
    # Remove if too short or clearly invalid
    if len(title) < 3:
        return None
    
    if title.lower() == 'unknown':
        return None
    
    return title


def enrich_job_data(row):
    """Enrich individual job record with validated/cleaned data."""
    row['company_name'] = normalize_company_name(row['company_name'])
    row['location'] = clean_location(row['location'])
    row['employment_type'] = clean_employment_type(row['employment_type'])
    
    # Ensure job_title is valid
    title = clean_job_title(row['job_title'])
    if not title:
        return None
    row['job_title'] = title
    
    # Ensure salary is valid
    if pd.isna(row['salary']) or row['salary'] == '':
        row['salary'] = 'Not specified'
    
    # Ensure skills are filled
    if pd.isna(row['required_skills']) or row['required_skills'] == '':
        row['required_skills'] = 'Not specified'
    
    return row


def filter_jobs_comprehensive(jobs_df):
    """Apply comprehensive filtering and cleaning to job dataset."""
    print("\n" + "="*70)
    print("COMPREHENSIVE JOB FILTERING & CLEANING")
    print("="*70)
    
    original_count = len(jobs_df)
    print(f"Starting with: {original_count} jobs")
    
    # 1. Remove exact duplicates by job_url
    jobs_df = jobs_df.drop_duplicates(subset=['job_url'], keep='first')
    print(f"✓ After removing duplicate URLs: {len(jobs_df)} jobs (removed {original_count - len(jobs_df)})")
    
    # 2. Remove rows with invalid job titles
    before = len(jobs_df)
    jobs_df = jobs_df[jobs_df['job_title'].apply(clean_job_title).notna()]
    print(f"✓ After removing invalid titles: {len(jobs_df)} jobs (removed {before - len(jobs_df)})")
    
    # 3. Remove rows with empty job descriptions
    before = len(jobs_df)
    jobs_df = jobs_df[jobs_df['job_description'].fillna('').str.strip() != '']
    print(f"✓ After removing empty descriptions: {len(jobs_df)} jobs (removed {before - len(jobs_df)})")
    
    # 4. Apply data enrichment and cleaning to each row
    print("\n✓ Normalizing company names, locations, and employment types...")
    jobs_df = jobs_df.apply(enrich_job_data, axis=1)
    jobs_df = jobs_df.dropna()  # Remove any rows that failed enrichment
    print(f"  {len(jobs_df)} jobs after data enrichment")
    
    # 5. Remove jobs with clearly corrupted data
    before = len(jobs_df)
    jobs_df = jobs_df[jobs_df['location'] != 'Unknown'].copy()  # Keep some location data
    # Actually, let's keep Unknown locations - they're valuable for RemoteOK jobs
    # Revert that:
    jobs_df = pd.concat([jobs_df, jobs_df[jobs_df['location'] == 'Unknown']], ignore_index=True)
    jobs_df = jobs_df.drop_duplicates(subset=['job_url'])
    
    # 6. Reset index
    jobs_df = jobs_df.reset_index(drop=True)
    
    removed_total = original_count - len(jobs_df)
    print(f"\n{'='*70}")
    print(f"Total removed: {removed_total} jobs")
    print(f"Final filtered dataset: {len(jobs_df)} jobs")
    print(f"{'='*70}")
    
    return jobs_df


def generate_summary(jobs_df):
    """Generate summary statistics of the filtered dataset."""
    print("\n" + "="*70)
    print("FINAL DATASET SUMMARY")
    print("="*70)
    
    print(f"\n📊 Total jobs: {len(jobs_df)}")
    
    print(f"\n📍 By company:")
    company_counts = jobs_df['company_name'].value_counts()
    for company, count in company_counts.items():
        pct = (count / len(jobs_df)) * 100
        print(f"  • {company}: {count} jobs ({pct:.1f}%)")
    
    print(f"\n💼 By employment type:")
    emp_counts = jobs_df['employment_type'].value_counts()
    for emp_type, count in emp_counts.items():
        if emp_type != 'Not specified':
            pct = (count / len(jobs_df)) * 100
            print(f"  • {emp_type}: {count} jobs ({pct:.1f}%)")
    
    print(f"\n🌍 Top 10 locations:")
    loc_counts = jobs_df['location'].value_counts().head(10)
    for loc, count in loc_counts.items():
        pct = (count / len(jobs_df)) * 100
        print(f"  • {loc}: {count} jobs ({pct:.1f}%)")
    
    print(f"\n🔧 Skills distribution (non-Unknown):")
    skills_df = jobs_df[jobs_df['required_skills'] != 'Not specified']
    if len(skills_df) > 0:
        print(f"  • Jobs with specific skills listed: {len(skills_df)} ({(len(skills_df)/len(jobs_df)*100):.1f}%)")
        print(f"  • Jobs without skills listed: {len(jobs_df) - len(skills_df)}")
    
    print("\n" + "="*70)


def main():
    jobs_path = Path("data") / "final" / "jobs.csv"
    backup_path = Path("data") / "final" / "jobs_backup.csv"
    output_path = Path("data") / "final" / "jobs.csv"
    
    if not jobs_path.exists():
        print(f"Error: {jobs_path} not found!")
        return
    
    print("\n" + "="*70)
    print("ADVANCED JOB DATASET ENHANCEMENT & FILTERING")
    print("="*70)
    
    # Load jobs
    df = pd.read_csv(jobs_path)
    print(f"\nLoaded: {len(df)} jobs from {jobs_path}")
    
    # Create backup
    df.to_csv(backup_path, index=False, encoding='utf-8-sig')
    print(f"✓ Backup saved to {backup_path}")
    
    # Apply comprehensive filtering
    df = filter_jobs_comprehensive(df)
    
    # Generate summary
    generate_summary(df)
    
    # Save filtered jobs
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\n✓ Saved {len(df)} enhanced & filtered jobs to {output_path}")
    print("\n✅ Job dataset enhancement and filtering complete!")


if __name__ == "__main__":
    main()
