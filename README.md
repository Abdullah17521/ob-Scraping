# Job Scraping Assignment (Stripe + Greenhouse)

This repository is a complete hybrid web-scraping architecture for Data Science:
- **Selenium** for dynamic page navigation and collecting company career board job links.
- **Scrapy** for structured crawling of each job detail page and extracting required fields.
- **Pandas analysis** for data cleaning, salary metrics, and skill/location insights.

## Hybrid Architecture
1. `/selenium/selenium_scrape.py` launches a headless browser, navigates each source, and extracts direct `/jobs/listing/` links.
2. `/scrapy_project/scrapy_project/spiders/job_spider.py` reads `data/raw/job_links.csv`, parses valid listing pages, and outputs raw jobs to `data/final/jobs.csv`.
3. `/analysis/clean_jobs.py` normalizes columns and writes `data/final/jobs_clean_final.csv`.
4. `/analysis/analyze_jobs.py` computes analytics and writes `analysis/insights.txt`.

## Folder Structure
- `/selenium`: Selenium collection scripts.
- `/scrapy_project`: Scrapy project files and spider.
- `/data/raw`: raw job links CSV.
- `/data/final`: raw and cleaned final datasets.
- `/analysis`: cleaning and analysis scripts.
- `/docs`: project documentation.

## Run the Pipeline
```bash
pip install -r requirements.txt
python selenium/selenium_scrape.py
cd scrapy_project && python -m scrapy crawl job_spider -o ../data/final/jobs.csv
cd ..
python analysis/clean_jobs.py
python analysis/analyze_jobs.py
```

## Expected Output
- `data/raw/job_links.csv`
- `data/final/jobs_clean_final.csv`
- `analysis/insights.txt`

## Git Workflow (Professional)
```bash
# 1) Start from main
git checkout main
git pull origin main

# 2) Create and work on feature branch
git checkout -b develop
# edit code, run tests
git add .
git commit -m "feat: implement hybrid scraper pipeline"

# 3) Push and open PR
git push -u origin develop
# create PR in GitHub from develop into main

# 4) Once approved and merged
git checkout main
git pull origin main

git checkout -b release/v1.0
# tag final release
git checkout main
git tag -a v1.0 -m "Release v1.0"
git push origin main --tags
```

## Notes
- Use only public job board pages.
- Keep scraping polite and respect robots policies.

