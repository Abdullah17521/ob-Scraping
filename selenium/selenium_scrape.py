import csv
import time
import random
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service


def safe_find_elements(driver, by, value):
    try:
        return driver.find_elements(by, value)
    except Exception:
        return []


def safe_find_element(driver, by, value):
    try:
        return driver.find_element(by, value)
    except Exception:
        return None


def scroll_to_bottom(driver, pause=1.0):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(pause + random.random())


def gather_greenhouse(driver, url, query, max_links=200):
    driver.get(url)
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(2)
    search = safe_find_element(driver, By.CSS_SELECTOR, "input[type='search']")
    if search and query:
        try:
            search.clear()
            search.send_keys(query)
            search.send_keys(Keys.ENTER)
            time.sleep(2)
        except Exception:
            pass

    links = set()
    last_count = 0
    for _ in range(35):
        scroll_to_bottom(driver, pause=1.0)
        for a in safe_find_elements(driver, By.XPATH, "//a[contains(@href, '/jobs/listing/') or contains(@href, '/jobs/')]"):
            href = a.get_attribute("href")
            if href and href.startswith("http") and "/jobs/" in href:
                href = href.split("#")[0]
                links.add(href.split("?")[0])
        if len(links) >= max_links:
            break
        if len(links) == last_count:
            break
        last_count = len(links)
    return list(links)


def gather_lever(driver, url, max_links=200):
    driver.get(url)
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(2)
    links = set()
    last_count = 0
    for _ in range(30):
        scroll_to_bottom(driver, pause=1.2)
        for a in safe_find_elements(driver, By.TAG_NAME, "a"):
            href = a.get_attribute("href")
            if href and 'lever.co' in href and ('/jobs/' in href or '/apply/' in href):
                links.add(href.split("?")[0])
        if len(links) >= max_links:
            break
        if len(links) == last_count:
            break
        last_count = len(links)
    return list(links)


def gather_ashby(driver, url, max_links=150):
    driver.get(url)
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(2)
    links = set()
    last_count = 0
    for _ in range(35):
        scroll_to_bottom(driver, pause=1.0)
        try:
            load = safe_find_element(driver, By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'load more')]")
            if load:
                driver.execute_script("arguments[0].click();", load)
                time.sleep(1.5)
        except Exception:
            pass
        for a in safe_find_elements(driver, By.XPATH, "//a[contains(@href,'/jobs/') or contains(@href,'/job/')]"):
            href = a.get_attribute("href")
            if href and href.startswith("http"):
                links.add(href.split("?")[0])
        if len(links) >= max_links:
            break
        if len(links) == last_count:
            break
        last_count = len(links)
    return list(links)


def main():
    output_path = Path(__file__).resolve().parent.parent / "data" / "raw" / "job_links.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    sources = [
        {"name": "Stripe", "company": "Stripe", "url": "https://boards.greenhouse.io/stripe", "type": "greenhouse", "query": "Software Engineer"},
        {"name": "Airbnb", "company": "Airbnb", "url": "https://boards.greenhouse.io/airbnb", "type": "greenhouse", "query": "Data"},
        {"name": "Square", "company": "Square", "url": "https://boards.greenhouse.io/square", "type": "greenhouse", "query": "Engineer"},
        {"name": "Netflix", "company": "Netflix", "url": "https://jobs.lever.co/netflix", "type": "lever", "query": ""},
        {"name": "Ashby", "company": "Ashby", "url": "https://jobs.ashbyhq.com", "type": "ashby", "query": ""},
    ]

    all_rows = []
    for source in sources:
        print(f"Scraping {source['name']} ({source['url']})")
        try:
            if source["type"] == "greenhouse":
                links = gather_greenhouse(driver, source["url"], source.get("query", ""), max_links=250)
            elif source["type"] == "lever":
                links = gather_lever(driver, source["url"], max_links=250)
            else:
                links = gather_ashby(driver, source["url"], max_links=180)
            links = list(dict.fromkeys(links))
        except Exception as e:
            print(f"  Failed to collect from {source['name']}: {e}")
            links = []
        print(f"  Collected {len(links)} links")
        for link in links:
            all_rows.append({
                "company": source["company"],
                "source": source["url"],
                "role_searched": source.get("query", ""),
                "job_url": link,
            })

    driver.quit()

    unique = {}
    for r in all_rows:
        if not r.get("job_url"):
            continue
        unique[r["job_url"]] = r

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["company", "source", "role_searched", "job_url"])
        writer.writeheader()
        for r in unique.values():
            writer.writerow(r)

    print(f"Saved {len(unique)} unique links to {output_path}")


if __name__ == "__main__":
    main()
