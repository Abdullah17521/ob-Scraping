import subprocess
import sys
from pathlib import Path


def run(cmd, cwd=None):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, text=True)
    if result.returncode != 0:
        print(f"Command failed: {cmd}")
        sys.exit(result.returncode)


def main():
    run("python selenium/selenium_scrape.py")
    run("python -m scrapy crawl job_spider -O ../data/final/jobs.csv", cwd="scrapy_project")
    run("python analysis/clean_jobs.py")
    run("python analysis/analyze_jobs.py")


if __name__ == '__main__':
    main()
