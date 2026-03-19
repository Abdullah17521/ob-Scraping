# Job Market Analysis Report

## Sources scraped
- Stripe (Greenhouse board)
- Airbnb (Greenhouse board)
- Square (Greenhouse board)

## Data collection
- Collected job links in `/data/raw/job_links.csv` using Selenium browser automation.
- Extracted structured job fields with Scrapy to `/data/final/jobs_clean_final.csv`.
- Joined job links metadata and job details into one final dataset: `/data/final/jobs_clean_final.csv`.

## Key Findings
- **Total jobs scraped**: 26 (after cleaning and filtering, as detailed in `/data/final/jobs_clean_final.csv`)
- **Top skills** strong presentation skills, ability to operate in ambiguous environment, technology interest, complex negotiations, communication skills, marketing, product knowledge, deal strategy, account mapping.
- **Top locations**: Toronto, South San Francisco HQ, New York, Dublin HQ (city-level breakdown available in the cleaned dataset).
- **Companies posting highest number of roles**: Stripe.
- **Entry-level/internship count**: 0 (no roles matched intern/junior/entry keywords).
- **Most common job titles/role families**: Account Executive, Partner Marketing Lead, AV Builds and Operations, Android Engineer, AI/ML Engineering Manager, Backend Engineer.

## Assumptions and compliance
- Scraped only public job listings.
- Did not bypass authentication or CAPTCHA.
- Added polite delays before each request.
- No personal data collected.

