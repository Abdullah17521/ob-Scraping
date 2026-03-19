import csv
import time
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


def collect_greenhouse_links(driver, url, query, limit=200):
    driver.get(url)
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(2)

    # Some boards support quick search by keyword param
    if "?" in url:
        pass
    # try filters by role using search box if present
    search = safe_find_element(driver, By.CSS_SELECTOR, "input[type='search']")
    if search:
        search.clear()
        search.send_keys(query)
        search.send_keys(Keys.ENTER)
        time.sleep(3)

    links = set()
    for _ in range(20):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        job_cards = safe_find_elements(driver, By.CSS_SELECTOR, "a[href*='/jobs/']")
        for card in job_cards:
            try:
                href = card.get_attribute("href")
                if href and "/jobs/" in href:
                    links.add(href.split("?")[0])
            except Exception:
                pass
        if len(links) >= limit:
            break
    return list(links)


def collect_lever_links(driver, url, query, limit=200):
    driver.get(url)
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(2)
    links = set()
    for _ in range(20):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        for a in safe_find_elements(driver, By.XPATH, "//a[contains(@href,'lever.co') and contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'apply')]"):
            href = a.get_attribute("href")
            if href:
                links.add(href.split("?")[0])
        for a in safe_find_elements(driver, By.XPATH, "//a[contains(@href,'lever.co') and contains(@href,'/#')]"):
            href = a.get_attribute("href")
            if href:
                links.add(href.split("?")[0])
        if len(links) >= limit:
            break
    return list(links)


def gather_links(driver, source):
    if source["type"] == "greenhouse":
        return gather_greenhouse_links(driver, source)
    return collect_lever_links(driver, source["url"], source["query"], limit=150)


def gather_greenhouse_links(driver, source):
    url = source["url"]
    query = source["query"]
    driver.get(url)
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(2)

    search = safe_find_element(driver, By.CSS_SELECTOR, "input[type='search']")
    if search:
        try:
            search.clear()
            search.send_keys(query)
            search.send_keys(Keys.ENTER)
            time.sleep(2)
        except Exception:
            pass

    links = set()
    for _ in range(25):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        anchors = safe_find_elements(driver, By.XPATH, "//a[contains(@href,'/jobs/listing/') or contains(@href,'/jobs/')]")
        for a in anchors:
            href = a.get_attribute("href")
            if not href or not href.startswith("http"):
                continue
            if "/jobs/listing/" not in href:
                continue
            exclude = ["/search", "/benefits", "/university", "/life-at-stripe"]
            if any(x in href for x in exclude):
                continue
            links.add(href.split("?")[0])
        if len(links) >= 200:
            break
    return list(links)


def main():
    script_root = Path(__file__).resolve().parent
    output_path = script_root.parent / "data" / "raw" / "job_links.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.maximize_window()

    sources = [
        {"company": "Stripe", "url": "https://boards.greenhouse.io/stripe", "type": "greenhouse", "query": "Software Engineer"},
        {"company": "Airbnb", "url": "https://boards.greenhouse.io/airbnb", "type": "greenhouse", "query": "Data Analyst"},
        {"company": "Square", "url": "https://boards.greenhouse.io/square", "type": "greenhouse", "query": "Intern"},
    ]

    all_rows = []
    for source in sources:
        print(f"Scraping {source['company']} {source['url']}")
        try:
            links = gather_links(driver, source)
            print(f"  Found {len(links)} links")
        except Exception as e:
            print(f"  Failed: {e}")
            links = []
        for link in links:
            all_rows.append({
                "company": source["company"],
                "source": source["url"],
                "role_searched": source["query"],
                "job_url": link,
            })

    driver.quit()

    unique = {r["job_url"]: r for r in all_rows if r.get("job_url")}
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["company", "source", "role_searched", "job_url"])
        writer.writeheader()
        for r in unique.values():
            writer.writerow(r)

    print(f"Saved {len(unique)} links to {output_path}")


if __name__ == "__main__":
    main()
