"""
Advanced noise removal and data quality filtering for job dataset.
Removes corrupted fields, invalid data, and standardizes formats.
"""
import pandas as pd
from pathlib import Path
import re
from datetime import datetime


def remove_emoji_and_corruption(text):
    """Remove emoji and corrupted characters from text."""
    if pd.isna(text):
        return text
    
    text = str(text)
    # Remove emoji
    text = text.encode('ascii', 'ignore').decode('ascii')
    # Remove common corruptions
    text = re.sub(r'[🎧🎯📱🌍📊💼🔧]', '', text)
    return text.strip()


def is_valid_department(dept):
    """Check if department is valid (not corrupted)."""
    if pd.isna(dept) or dept == '':
        return False
    
    dept = str(dept).strip()
    
    # Remove emoji versions
    if any(emoji in dept for emoji in ['🎧', '🎯', '📱', '🌍']):
        return False
    
    # Remove date-like corruption
    if any(x in dept for x in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun', 'GMT', '+0000']):
        return False
    
    # Must have at least some length
    if len(dept) < 3:
        return False
    
    return True


def clean_experience_level(exp_level):
    """Clean experience level - remove corrupted numeric values."""
    if pd.isna(exp_level) or exp_level == '':
        return 'Not specified'
    
    exp_level = str(exp_level).strip()
    
    # Valid values
    valid_levels = ['Junior', 'Mid-level', 'Senior', 'Lead', 'Manager', 'Executive', 'Entry-Level', 'Internship']
    
    if exp_level in valid_levels:
        return exp_level
    
    # Check if it's corrupted (looks like a number from other fields)
    if exp_level.isdigit() or (exp_level[0].isdigit() and '+' in exp_level):
        return 'Not specified'
    
    # If contains only numbers and symbols, it's corrupted
    if re.match(r'^[\d+\-,]*$', exp_level):
        return 'Not specified'
    
    return 'Not specified'


def clean_salary(salary):
    """Clean and standardize salary format."""
    if pd.isna(salary) or salary == '':
        return 'Not specified'
    
    salary = str(salary).strip()
    
    # Remove corrupted single values like "$1.4"
    if salary.startswith('$') and salary.count('$') == 1 and '-' not in salary and ',' not in salary and ' ' not in salary:
        if len(salary) < 5:
            return 'Not specified'
    
    # Check if it looks like a valid salary
    if not any(c in salary for c in ['$', '€', '£', 'k', 'K']):
        if salary != 'Not specified':
            return 'Not specified'
    
    # Standardize spacing in ranges
    salary = re.sub(r',+', ',', salary)
    
    return salary


def clean_job_description(desc):
    """Validate job description length."""
    if pd.isna(desc) or desc == '':
        return None
    
    desc = str(desc).strip()
    
    # Remove if too short (likely corrupted)
    if len(desc) < 30:
        return None
    
    return desc


def standardize_date(date_str):
    """Standardize date format to YYYY-MM-DD."""
    if pd.isna(date_str) or date_str == '':
        return 'Unknown'
    
    date_str = str(date_str).strip()
    
    # Try to parse ISO format with timezone
    if 'T' in date_str and '+' in date_str:
        try:
            date_obj = datetime.fromisoformat(date_str.replace('+00:00', ''))
            return date_obj.strftime('%Y-%m-%d')
        except:
            pass
    
    # Try to parse ISO format without timezone
    if 'T' in date_str:
        try:
            date_obj = datetime.fromisoformat(date_str)
            return date_obj.strftime('%Y-%m-%d')
        except:
            pass
    
    # Try existing date format
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%Y-%m-%d')
    except:
        pass
    
    return date_str


def clean_location(location):
    """Clean and validate location field - remove obvious corruptions."""
    if pd.isna(location) or location == '':
        return 'Unknown'
    
    location = str(location).strip()
    
    # Remove clearly corrupted entries
    corrupted_keywords = ['Investment', 'Department', 'Engineer I', 'Support jobs', 'vestment']
    for keyword in corrupted_keywords:
        if keyword in location:
            return 'Other'
    
    # Remove RSS/feed artifacts
    if location.endswith('.rss') or location.endswith('.xml'):
        return 'Unknown'
    
    # Remove emoji
    location = location.replace('🎧', '').strip()
    
    return location if location else 'Unknown'


def filter_and_clean_dataset(jobs_df):
    """Apply comprehensive noise removal and cleaning."""
    print("\n" + "="*70)
    print("COMPREHENSIVE NOISE REMOVAL & DATA QUALITY FILTERING")
    print("="*70)
    
    original_count = len(jobs_df)
    print(f"\nStarting with: {original_count} jobs")
    
    # 1. Clean corrupted text fields
    print("\n✓ Step 1: Removing emoji and corrupted characters...")
    jobs_df['department'] = jobs_df['department'].apply(remove_emoji_and_corruption)
    jobs_df['job_title'] = jobs_df['job_title'].apply(remove_emoji_and_corruption)
    jobs_df['location'] = jobs_df['location'].apply(clean_location)  # Use proper location cleaning
    
    # 2. Remove rows with invalid departments
    print("✓ Step 2: Removing rows with corrupted department data...")
    before = len(jobs_df)
    jobs_df = jobs_df[jobs_df['department'].apply(is_valid_department)]
    removed = before - len(jobs_df)
    print(f"  Removed {removed} rows with corrupted departments")
    
    # 3. Clean experience level
    print("✓ Step 3: Cleaning experience level field...")
    jobs_df['experience_level'] = jobs_df['experience_level'].apply(clean_experience_level)
    
    # 4. Clean salary field
    print("✓ Step 4: Cleaning salary field...")
    jobs_df['salary'] = jobs_df['salary'].apply(clean_salary)
    
    # 5. Validate job descriptions
    print("✓ Step 5: Validating job descriptions...")
    before = len(jobs_df)
    jobs_df = jobs_df[jobs_df['job_description'].apply(clean_job_description).notna()]
    removed = before - len(jobs_df)
    print(f"  Removed {removed} rows with short/incomplete descriptions")
    
    # 6. Standardize date format
    print("✓ Step 6: Standardizing date format...")
    jobs_df['posted_date'] = jobs_df['posted_date'].apply(standardize_date)
    
    # 7. Remove any rows still with short job titles
    print("✓ Step 7: Validating job titles...")
    before = len(jobs_df)
    jobs_df = jobs_df[jobs_df['job_title'].str.len() >= 3]
    removed = before - len(jobs_df)
    print(f"  Removed {removed} rows with invalid titles")
    
    # 8. Remove exact duplicates
    print("✓ Step 8: Removing exact duplicates...")
    before = len(jobs_df)
    jobs_df = jobs_df.drop_duplicates(subset=['job_url', 'job_title'], keep='first')
    removed = before - len(jobs_df)
    print(f"  Removed {removed} exact duplicates")
    
    # 9. Reset index
    jobs_df = jobs_df.reset_index(drop=True)
    
    print(f"\n{'='*70}")
    total_removed = original_count - len(jobs_df)
    print(f"Total removed: {total_removed} rows")
    print(f"Final dataset: {len(jobs_df)} jobs")
    print(f"{'='*70}\n")
    
    return jobs_df


def generate_quality_report(jobs_df):
    """Generate data quality report after cleaning."""
    print("\n" + "="*70)
    print("DATA QUALITY REPORT - AFTER CLEANING")
    print("="*70)
    
    print(f"\n📊 Total Jobs: {len(jobs_df)}")
    
    print(f"\n🏢 Companies:")
    for company, count in jobs_df['company_name'].value_counts().items():
        print(f"  • {company}: {count} jobs")
    
    print(f"\n💼 Employment Types:")
    for emp_type, count in jobs_df['employment_type'].value_counts().items():
        print(f"  • {emp_type}: {count} jobs")
    
    print(f"\n📈 Experience Levels:")
    for exp_level, count in jobs_df['experience_level'].value_counts().items():
        print(f"  • {exp_level}: {count} jobs")
    
    print(f"\n📁 Departments (top 10):")
    for dept, count in jobs_df['department'].value_counts().head(10).items():
        print(f"  • {dept}: {count} jobs")
    
    print(f"\n💰 Salary Distribution:")
    salary_counts = jobs_df['salary'].value_counts()
    print(f"  • With salary: {(salary_counts != 'Not specified').sum()} jobs")
    print(f"  • Without salary: {(salary_counts == 'Not specified').sum()} jobs")
    
    print(f"\n📄 Job Description Quality:")
    df_copy = jobs_df.copy()
    df_copy['desc_len'] = df_copy['job_description'].str.len()
    print(f"  • Min length: {df_copy['desc_len'].min()} chars")
    print(f"  • Max length: {df_copy['desc_len'].max()} chars")
    print(f"  • Avg length: {df_copy['desc_len'].mean():.0f} chars")
    
    print(f"\n📅 Date Range:")
    print(f"  • Earliest: {jobs_df['posted_date'].min()}")
    print(f"  • Latest: {jobs_df['posted_date'].max()}")
    
    print(f"\n✅ Data Completeness:")
    null_counts = jobs_df.isnull().sum()
    total_fields = len(jobs_df) * len(jobs_df.columns)
    null_total = null_counts.sum()
    completeness = ((total_fields - null_total) / total_fields) * 100
    print(f"  • Completeness: {completeness:.1f}%")
    
    print("\n" + "="*70 + "\n")


def main():
    jobs_path = Path("data") / "final" / "jobs.csv"
    backup_path = Path("data") / "final" / "jobs_pre_cleanup.csv"
    output_path = Path("data") / "final" / "jobs.csv"
    
    if not jobs_path.exists():
        print(f"Error: {jobs_path} not found!")
        return
    
    print("\n" + "="*70)
    print("ADVANCED JOB DATA NOISE REMOVAL")
    print("="*70)
    
    # Load jobs
    df = pd.read_csv(jobs_path)
    print(f"\nLoaded: {len(df)} jobs from {jobs_path}")
    
    # Create backup
    df.to_csv(backup_path, index=False, encoding='utf-8-sig')
    print(f"✓ Backup saved to {backup_path}")
    
    # Apply comprehensive filtering
    df = filter_and_clean_dataset(df)
    
    # Generate quality report
    generate_quality_report(df)
    
    # Save cleaned jobs
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"✓ Saved {len(df)} cleaned jobs to {output_path}")
    print("\n✅ Noise removal and data quality filtering complete!")


if __name__ == "__main__":
    main()
