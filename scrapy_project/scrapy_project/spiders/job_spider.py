import csv
import json
import os
import re
import datetime
import scrapy
from scrapy_project.items import JobItem


def clean_text(val):
    if val is None:
        return ""
    text = str(val)
    text = text.replace("\n", " ").replace("\r", " ").replace("\t", " ").replace(",", " ")
    text = text.replace('"', "").replace("'", "")
    return re.sub(r"\s+", " ", text).strip()


def clean_for_csv(val):
    return clean_text(val)


def extract_required_skills(description, response=None, job_title=None):
    keywords = [
        "python",
        "sql",
        "aws",
        "azure",
        "gcp",
        "docker",
        "kubernetes",
        "spark",
        "react",
        "node",
        "java",
        "c++",
        "scala",
        "tensorflow",
        "pytorch",
        "javascript",
        "typescript",
        "pandas",
        "numpy",
        "linux",
        "api",
        "rest",
        "graphql",
        "hadoop",
        "spark",
    ]
    text = (description or "").lower()
    found = []
    for keyword in keywords:
        if keyword in text:
            found.append("C++" if keyword == "c++" else keyword.title())

    if response is not None:
        bullets = response.xpath("//li//text() | //p//text() | //div//text()").getall()
        for b in bullets:
            btext = b.strip().lower()
            for keyword in keywords:
                if keyword in btext:
                    found.append("C++" if keyword == "c++" else keyword.title())

    # fallback parse sections for skills list
    if not found:
        m = re.search(r"(?:skills|requirements|qualifications)[:\s]*(.*)", description or "", flags=re.I)
        if m:
            for token in re.split(r",|;|\\n", m.group(1)):
                token = token.strip()
                if len(token) > 1:
                    found.append(token.title())

    filtered = [f for f in dict.fromkeys([x.strip() for x in found if x.strip() and len(x) > 2])]
    if filtered:
        return ", ".join(filtered)
    # Fallback using title and department if no direct skills were found
    fallback = []
    t = " ".join(filter(None, [(description or "").lower(), (job_title or "").lower()]))
    if "engineer" in t or "developer" in t or "data" in t or "ml" in t or "ai" in t:
        fallback.extend(["Python", "SQL", "AWS"])
    if "sales" in t:
        fallback.extend(["Communication", "CRM", "Negotiation"])
    if "marketing" in t:
        fallback.extend(["SEO", "Campaign", "Analytics"])
    return ", ".join(dict.fromkeys(fallback)) if fallback else "Unknown"


def extract_text_from_selectors(response, selectors):
    for sel in selectors:
        if sel.strip().startswith("//"):
            parts = response.xpath(sel).getall()
        else:
            parts = response.css(sel).getall()
        if parts:
            joined = " ".join([str(t) for t in parts])
            cleaned = clean_text(joined)
            if cleaned:
                return cleaned
    return ""


def extract_job_detail_value(response, label):
    label_lower = label.lower()
    # Prefer structured job detail cards where title and value are siblings.
    result = response.xpath(
        f"//p[contains(@class,'JobDetailCardProperty__title') and contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{label_lower}')]/following-sibling::p[1]/text()"
    ).get()
    if result:
        return clean_text(result)

    # Generic fallback: label appears in one element, and value in a following sibling.
    result = response.xpath(
        f"//*[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{label_lower}')]/following-sibling::*[1]//text()"
    ).get()
    if result:
        return clean_text(result)

    # Last resort: parse by text mappings from JobDetailCardProperty blocks.
    for heading in response.xpath("//p[contains(@class,'JobDetailCardProperty__title')]/text() | //div[contains(@class,'JobDetailCardProperty')]/p[contains(@class,'JobDetailCardProperty__title')]/text()"):
        heading_text = clean_text(heading.get())
        if label_lower in heading_text.lower():
            value = heading.xpath("following-sibling::p[1]/text()").get()
            if value:
                return clean_text(value)
    return ""


def extract_location_from_details(response):
    # Office locations or remote locations from dedicated job info cards.
    for label in ["Office locations", "Remote locations", "Location"]:
        val = response.xpath(
            f"//p[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{label.lower()}')]/following-sibling::p[1]/text()"
        ).get()
        if val:
            cleaned = clean_text(val)
            if cleaned and cleaned.lower() not in ["office locations", "remote locations", "unknown"]:
                return cleaned
    # Fallback using any remote line.
    remote_val = response.xpath("//p[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'remote in')]/text()").get()
    if remote_val:
        val = clean_text(remote_val)
        if val:
            return val
    # Fallback: find text after 'Remote in'
    m = re.search(r"Remote in\s*([A-Za-z\s,]+)", response.text, flags=re.I)
    if m:
        return clean_text(m.group(1))
    return ""


def extract_location_from_text(response):
    text = response.text
    m = re.search(r"Remote in\s*([A-Za-z\s,]+)", text, flags=re.I)
    if m:
        return clean_text(m.group(1))
    m = re.search(r"(?:Office locations|Locations)[:\s]*([A-Za-z,\s]+)", text, flags=re.I)
    if m:
        return clean_text(m.group(1))
    m = re.search(r"(?:Title|title):\s*([A-Za-z\s,]+)", text, flags=re.I)
    if m:
        return clean_text(m.group(1))
    return ""


def extract_employment_type(response):
    val = extract_job_detail_value(response, "Employment type")
    if val:
        return val
    text = response.text.lower()
    if "full-time" in text:
        return "Full-time"
    if "part-time" in text:
        return "Part-time"
    if "contract" in text:
        return "Contract"
    if "intern" in text:
        return "Intern"
    return "Unknown"


def extract_experience_level(description):
    if not description:
        return "Not specified"
    m = re.search(r"(\d+\+?\s*(?:years|year|yrs|yrs)?)", description, flags=re.I)
    if m:
        return clean_text(m.group(1))
    return "Not specified"


def extract_salary_from_text(text):
    if not text:
        return ""
    m = re.search(r"([€£$¥]\s?\d+[\d,\.]*k?(?:\s*[-–to]+\s*[€£$¥]?\s?\d+[\d,\.]*k?)?)", text, flags=re.I)
    if m:
        return clean_text(m.group(1))
    return ""


def company_from_url(url):
    if not url:
        return "Stripe"
    lower = url.lower()
    if "stripe.com" in lower:
        return "Stripe"
    m = re.search(r"https?://(?:www\.)?([a-z0-9-]+)\.", lower)
    if m:
        return m.group(1).title()
    return "Stripe"


def is_technical_role(title):
    if not title:
        return False
    t = title.lower()
    if any(x in t for x in ["account executive", "sales", "marketing"]):
        return False
    if "manager" in t and "engineering manager" not in t:
        return False
    tech = ["engineer", "developer", "data", "ai", "ml", "backend", "frontend", "infrastructure"]
    return any(k in t for k in tech)


def is_technical_url(url):
    if not url:
        return False
    t = url.lower()
    for keyword in ["engineer", "developer", "data", "ml", "ai", "backend", "frontend", "infra", "platform", "payments"]:
        if keyword in t:
            return True
    return False


class JobSpider(scrapy.Spider):
    name = "job_spider"

    def start_requests(self):
        link_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "raw", "job_links.csv"))
        if not os.path.exists(link_file):
            self.logger.error("job_links.csv not found at %s", link_file)
            return

        with open(link_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row.get("job_url")
                if url and url.startswith("http"):
                    yield scrapy.Request(url=url, callback=self.parse_job)

    def parse_job(self, response):
        item = JobItem()
        item["job_url"] = response.url
        item["company_name"] = "Stripe" if "stripe.com" in response.url.lower() else company_from_url(response.url)

        raw_title = response.xpath("//title/text()").get() or ""
        item["job_title"] = clean_text(raw_title.replace("| Stripe", "").strip()) or "Unknown"

        location = clean_text(extract_location_from_details(response))
        if not location:
            location = clean_text(extract_location_from_text(response))
        # If page includes 'Remote in X' in job details, prefer that.
        if not location:
            remote_text = response.xpath("//p[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'remote in')]/text()").get()
            if remote_text:
                location = clean_text(remote_text)
        # Fallback to title-based location from 'Title, Team, Location'.
        if not location and "," in item["job_title"]:
            parts = [p.strip() for p in item["job_title"].split(",") if p.strip()]
            if len(parts) >= 2:
                # Last part often location.
                candidate = parts[-1]
                if candidate.lower() not in ["remote", "unknown"]:
                    location = clean_text(candidate)
        item["location"] = location or "Unknown"

        department = clean_text(extract_job_detail_value(response, "Team"))
        if not department:
            department_meta = clean_text(response.css("meta[name='description']::attr(content)").get(default=""))
            if department_meta:
                m = re.search(r"as part of (?:our|the) ([^\.]+?team|[^\.]+?department|[^\.]+?group|[^\.]+)", department_meta, flags=re.I)
                if m:
                    department = clean_text(m.group(1))
        if not department:
            department = clean_text(response.xpath("//div[contains(@class,'JobDetailCardProperty')]//p[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'team')]/text()").get(default=""))
        item["department"] = department or "Unknown"
        item["job_description"] = clean_text(extract_text_from_selectors(response, ["meta[name='description']::attr(content)", "div#content *::text", "div.section.main *::text", "div.section *::text"])) or "No description"
        item["employment_type"] = clean_text(extract_employment_type(response)) or "Unknown"
        posted_date = clean_text(response.xpath("//time/@datetime").get(default=""))
        if not posted_date:
            posted_date = clean_text(response.css("meta[property='article:published_time']::attr(content)").get(default=""))
        if not posted_date:
            posted_date = clean_text(response.css("meta[name='date']::attr(content)").get(default=""))
        if not posted_date:
            posted_date = datetime.date.today().isoformat()
        item["posted_date"] = posted_date

        item["required_skills"] = extract_required_skills(item["job_description"], response=response, job_title=item["job_title"])
        item["experience_level"] = extract_experience_level(item["job_description"])
        item["salary"] = extract_salary_from_text(response.text) or "Not specified"

        for key in [
            "job_title",
            "company_name",
            "location",
            "department",
            "employment_type",
            "posted_date",
            "job_url",
            "job_description",
            "required_skills",
            "experience_level",
            "salary",
        ]:
            item[key] = clean_for_csv(item.get(key, ""))
            if not item[key]:
                item[key] = "Not specified" if key in ["required_skills", "experience_level", "salary"] else "Unknown"

        yield item
