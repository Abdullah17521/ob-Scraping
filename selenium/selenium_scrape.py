import csv
import time
import random
import re
import requests
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


def safe_get(driver, url, retries=4, pause=2):
    backoff = pause
    for i in range(retries):
        try:
            driver.get(url)
            return True
        except Exception as e:
            print(f"    safe_get failed attempt {i+1}/{retries} for {url}: {e}")
            if i == retries - 1:
                break
            time.sleep(backoff)
            backoff *= 2
    return False


def scroll_to_bottom(driver, pause=1.0):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(pause + random.random())


def gather_greenhouse(driver, url, query, max_links=300):
    links = set()
    if not safe_get(driver, url, retries=3, pause=3):
        print(f"  Greenhouse scraping failed for {url}: could not load page")
        return []
    try:
        driver.set_page_load_timeout(40)
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)
    except Exception:
        pass

    # Accept cookies/popups if any
    for _ in range(3):
        try:
            btn = safe_find_element(driver, By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree')]")
            if btn:
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(1)
        except Exception:
            break

    if query:
        try:
            search = safe_find_element(driver, By.CSS_SELECTOR, "input[type='search']")
            if search:
                search.clear()
                search.send_keys(query)
                search.send_keys(Keys.ENTER)
                time.sleep(2)
        except Exception:
            pass

    last_count = 0
    for _ in range(35):
        scroll_to_bottom(driver, pause=1.3)
        anchors = safe_find_elements(driver, By.XPATH, "//a[contains(@href, '/jobs/listing/') or contains(@href, '/jobs/') or contains(@href, '/job/')]" )
        if not anchors:
            anchors = safe_find_elements(driver, By.TAG_NAME, "a")
        for a in anchors:
            try:
                href = a.get_attribute("href")
            except Exception:
                continue
            if href and href.startswith("http") and ("/jobs/" in href or "/job/" in href):
                h = href.split("#")[0].split("?")[0]
                links.add(h)
        if len(links) >= max_links:
            break
        if len(links) == last_count:
            time.sleep(1.2)
            if len(links) == last_count:
                break
        last_count = len(links)
    return list(links)


def gather_remoteok(driver, url, max_links=260):
    links = set()
    if not safe_get(driver, url, retries=3, pause=3):
        print(f"  RemoteOK scraping failed for {url}: could not load page")
        return []
    driver.set_page_load_timeout(45)
    inject_stealth(driver)
    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table#jobsboard, .jobsboard")))
    except Exception:
        pass
    time.sleep(2)

    last_count = 0
    for _ in range(35):
        scroll_to_bottom(driver, pause=1.2)
        try:
            anchors = safe_find_elements(driver, By.XPATH, "//a[contains(@href, '/remote-jobs/')]")
        except Exception:
            anchors = []
        for a in anchors:
            try:
                href = a.get_attribute("href")
            except Exception:
                continue
            if href and href.startswith("http") and "/remote-jobs/" in href:
                links.add(href.split("#")[0].split("?")[0])
        if len(links) >= max_links:
            break
        if len(links) == last_count:
            break
        last_count = len(links)
    return list(links)[:max_links]


def gather_wwr_fallback(url, max_links=260):
    links = set()
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"}, timeout=20)
        html = resp.text
        for match in re.findall(r'href\s*=\s*"([^"]+)"', html):
            href = match.strip()
            if href.startswith("/"):
                href = "https://weworkremotely.com" + href
            if "weworkremotely.com" in href and any(k in href for k in ["/remote-jobs", "/jobs", "/categories", "/remote-"]):
                links.add(href.split("#")[0].split("?")[0])
    except Exception:
        return []
    return list(links)[:max_links]


def gather_wwr(driver, url, max_links=260):
    links = set()
    if not safe_get(driver, url, retries=3, pause=3):
        print(f"  WWR scraping failed for {url}: could not load page")
        return []
    driver.set_page_load_timeout(45)
    inject_stealth(driver)
    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except Exception:
        pass
    time.sleep(2)

    last_count = 0
    for _ in range(25):
        scroll_to_bottom(driver, pause=1.0)
        anchors = safe_find_elements(driver, By.XPATH, "//a")
        for a in anchors:
            try:
                href = a.get_attribute("href")
            except Exception:
                continue
            if not href:
                continue
            if href.startswith("/"):
                href = "https://weworkremotely.com" + href
            if "weworkremotely.com" not in href:
                continue
            if any(x in href for x in ["/remote-jobs", "/jobs", "/categories", "/remote-"]):
                links.add(href.split("#")[0].split("?")[0])
        if len(links) >= max_links:
            break
        if len(links) == last_count:
            break
        last_count = len(links)

    if len(links) < 15:
        fallback = gather_wwr_fallback(url, max_links=max_links)
        for f in fallback:
            links.add(f)

    filtered = [l for l in links if "/remote-jobs" in l or "/jobs" in l or "/categories" in l]
    return filtered[:max_links]


def filter_data_science_candidates(rows):
    keywords = ["data", "scientist", "ai", "engineer", "ml", "developer", "software", "platform"]
    filtered = []
    for r in rows:
        target_text = " ".join([
            str(r.get("job_url", "")), 
            str(r.get("title", "")), 
            str(r.get("anchor_text", "")), 
            str(r.get("source", ""))
        ]).lower()
        # For WWR and RemoteOK links, be more lenient (they're already from data-focused pages)
        if any(domain in target_text for domain in ["remoteok.com", "weworkremotely.com"]):
            filtered.append(r)
        elif any(k in target_text for k in keywords):
            filtered.append(r)
    return filtered


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
        {"name": "RemoteOK", "company": "RemoteOK", "url": "https://remoteok.com/remote-data-science-jobs", "type": "remoteok", "query": ""},
        {"name": "WWR", "company": "We Work Remotely", "url": "https://weworkremotely.com/categories/remote-data-science-ai-jobs", "type": "wwr", "query": ""},
    ]

    all_rows = []
    for source in sources:
        print(f"Scraping {source['name']} ({source['url']})")
        try:
            if source["type"] == "greenhouse":
                links = gather_greenhouse(driver, source["url"], source.get("query", ""), max_links=260)
            elif source["type"] == "remoteok":
                links = gather_remoteok(driver, source["url"], max_links=260)
            elif source["type"] == "wwr":
                links = gather_wwr(driver, source["url"], max_links=260)
            else:
                links = []
            links = list(dict.fromkeys(links))
        except Exception as e:
            print(f"  Failed to collect from {source['name']}: {e}")
            links = []
        print(f"  Collected {len(links)} links")
        for link in links:
            all_rows.append({
                "company": source["company"],
                "source_url": source["url"],
                "job_url": link,
                "anchor_text": "",
                "title": "",
            })

    driver.quit()

    filtered_rows = filter_data_science_candidates(all_rows)
    unique_by_url = {}
    for r in filtered_rows:
        if not r.get("job_url"):
            continue
        unique_by_url[r["job_url"]] = r

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["company", "source_url", "job_url"])
        writer.writeheader()
        for r in unique_by_url.values():
            writer.writerow({
                "company": r["company"],
                "source_url": r["source_url"],
                "job_url": r["job_url"],
            })

    print(f"Saved {len(unique_by_url)} unique filtered links to {output_path}")


if __name__ == "__main__":
    main()
