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


def inject_stealth(driver):
    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        })
    except Exception:
        pass


def scroll_to_bottom(driver, pause=1.0):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(pause + random.random())


def gather_greenhouse(driver, url, query, max_links=200):
    links = set()
    try:
        driver.get(url)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)
        search = safe_find_element(driver, By.CSS_SELECTOR, "input[type='search']")
    except Exception as e:
        print(f"  Greenhouse scraping failed for {url}: {e}")
        return []
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
    links = set()
    try:
        driver.get(url)
        inject_stealth(driver)
        try:
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".posting")))
        except Exception:
            pass
        time.sleep(2)

        last_count = 0
        for i in range(15):
            for a in safe_find_elements(driver, By.CSS_SELECTOR, "a.posting-title"):
                href = a.get_attribute("href")
                if href and href.startswith("http") and "/jobs/" in href:
                    links.add(href.split("?")[0])
            for a in safe_find_elements(driver, By.TAG_NAME, "a"):
                href = a.get_attribute("href")
                if href and href.startswith("http") and "/jobs/" in href:
                    links.add(href.split("?")[0])
            if len(links) >= max_links or len(links) == last_count:
                break
            last_count = len(links)
            scroll_to_bottom(driver, pause=1.0)
    except Exception as e:
        print(f"  Lever scraping failed for {url}: {e}")
    return list(links)[:max_links]


def gather_ashby(driver, url, max_links=180):
    links = set()
    try:
        driver.get(url)
        inject_stealth(driver)
        WebDriverWait(driver, 25).until(EC.element_to_be_clickable((By.TAG_NAME, "a")))
        time.sleep(2)

        for _ in range(12):
            # click load more if present
            for btn_text in ["Show More", "Load More", "Show more", "load more"]:
                try:
                    btn = safe_find_element(driver, By.XPATH, f"//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{btn_text.lower()}')]")
                    if btn:
                        driver.execute_script("arguments[0].click();", btn)
                        time.sleep(1)
                except Exception:
                    pass
            scroll_to_bottom(driver, pause=1.0)

        for a in safe_find_elements(driver, By.TAG_NAME, "a"):
            href = a.get_attribute("href")
            if href and "jobs.ashbyhq.com" in href and "/job/" in href:
                links.add(href.split("?")[0])
    except Exception as e:
        print(f"  Ashby scraping failed for {url}: {e}")
    return list(links)[:max_links]


def main():
    output_path = Path(__file__).resolve().parent.parent / "data" / "raw" / "job_links.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    inject_stealth(driver)

    sources = [
        {"name": "Stripe", "company": "Stripe", "url": "https://boards.greenhouse.io/stripe", "type": "greenhouse", "query": "Software Engineer"},
        {"name": "Airbnb", "company": "Airbnb", "url": "https://boards.greenhouse.io/airbnb", "type": "greenhouse", "query": "Data"},
        {"name": "Square", "company": "Square", "url": "https://boards.greenhouse.io/square", "type": "greenhouse", "query": "Engineer"},
        {"name": "Netflix", "company": "Netflix", "url": "https://jobs.lever.co/netflix", "type": "lever", "query": ""},
        {"name": "Palantir", "company": "Palantir", "url": "https://jobs.lever.co/palantir", "type": "lever", "query": ""},
        {"name": "Spotify", "company": "Spotify", "url": "https://jobs.lever.co/spotify", "type": "lever", "query": ""},
        {"name": "Vercel", "company": "Vercel", "url": "https://jobs.ashbyhq.com/vercel", "type": "ashby", "query": ""},
        {"name": "Duolingo", "company": "Duolingo", "url": "https://jobs.ashbyhq.com/duolingo", "type": "ashby", "query": ""},
        {"name": "Replicate", "company": "Replicate", "url": "https://jobs.ashbyhq.com/replicate", "type": "ashby", "query": ""},
    ]

    all_rows = []
    for source in sources:
        print(f"Scraping {source['name']} ({source['url']})")
        try:
            if source["type"] == "greenhouse":
                links = gather_greenhouse(driver, source["url"], source.get("query", ""), max_links=250)
            elif source["type"] == "lever":
                links = gather_lever(driver, source["url"], max_links=250)
            elif source["type"] == "ashby":
                links = gather_ashby(driver, source["url"], max_links=180)
            else:
                links = gather_greenhouse(driver, source["url"], source.get("query", ""), max_links=250)
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
