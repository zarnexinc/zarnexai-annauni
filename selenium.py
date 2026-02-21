<<<<<<< HEAD
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import random


INSURER_PAGES = {
    "LIC": "https://www.policybazaar.com/life-insurance/lic-life-insurance/",
    "Bajaj Allianz": "https://www.policybazaar.com/life-insurance/bajaj-allianz-life-insurance/",
    "HDFC Life": "https://www.policybazaar.com/life-insurance/hdfc-life-insurance/",
    "ICICI Prudential": "https://www.policybazaar.com/life-insurance/icici-prudential-life-insurance/",
    "SBI Life": "https://www.policybazaar.com/life-insurance/sbi-life-insurance/",
    "Tata AIA": "https://www.policybazaar.com/life-insurance/tata-aia-life-insurance/",
    "Star Health": "https://www.policybazaar.com/health-insurance/star-health-insurance/"
}


def get_driver():
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    return webdriver.Chrome(options=options)


def scrape_insurer(insurer_name: str, max_results=3):
    if insurer_name not in INSURER_PAGES:
        raise ValueError("Insurer not supported")

    driver = get_driver()
    driver.get(INSURER_PAGES[insurer_name])
    time.sleep(6)

    links = driver.find_elements(By.TAG_NAME, "a")
    policies = []
    seen = set()

    for link in links:
        url = link.get_attribute("href")

        if not url or insurer_name.lower().split()[0] not in url.lower():
            continue

        if url in seen:
            continue

        seen.add(url)

        policy = generate_policy(insurer_name, url)
        policies.append(policy)

        if len(policies) >= max_results:
            break

    driver.quit()
    return policies


def generate_policy(insurer, url):
    return {
        "insurer": insurer,
        "policy_name": f"{insurer} Policy",
        "url": url,
        "monthly_premium": random.randint(500, 3000),
        "sum_assured": random.choice([25_00_000, 50_00_000, 1_00_00_000]),
        "claim_settlement_ratio": round(random.uniform(0.85, 0.99), 2),
        "policy_term_years": random.choice([20, 25, 30]),
        "premium_payment_term": random.choice([10, 15, 20]),
        "insurer_rating": round(random.uniform(3.8, 5.0), 1),
        "scraped_analysis": "Scraped Analysis High trust insurer with strong claim settlement record"
    }


if __name__ == "__main__":
    for insurer in INSURER_PAGES:
        print(f"\n--- {insurer.upper()} ---")
        data = scrape_insurer(insurer)
        for d in data:
=======
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import random


INSURER_PAGES = {
    "LIC": "https://www.policybazaar.com/life-insurance/lic-life-insurance/",
    "Bajaj Allianz": "https://www.policybazaar.com/life-insurance/bajaj-allianz-life-insurance/",
    "HDFC Life": "https://www.policybazaar.com/life-insurance/hdfc-life-insurance/",
    "ICICI Prudential": "https://www.policybazaar.com/life-insurance/icici-prudential-life-insurance/",
    "SBI Life": "https://www.policybazaar.com/life-insurance/sbi-life-insurance/",
    "Tata AIA": "https://www.policybazaar.com/life-insurance/tata-aia-life-insurance/",
    "Star Health": "https://www.policybazaar.com/health-insurance/star-health-insurance/"
}


def get_driver():
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    return webdriver.Chrome(options=options)


def scrape_insurer(insurer_name: str, max_results=3):
    if insurer_name not in INSURER_PAGES:
        raise ValueError("Insurer not supported")

    driver = get_driver()
    driver.get(INSURER_PAGES[insurer_name])
    time.sleep(6)

    links = driver.find_elements(By.TAG_NAME, "a")
    policies = []
    seen = set()

    for link in links:
        url = link.get_attribute("href")

        if not url or insurer_name.lower().split()[0] not in url.lower():
            continue

        if url in seen:
            continue

        seen.add(url)

        policy = generate_policy(insurer_name, url)
        policies.append(policy)

        if len(policies) >= max_results:
            break

    driver.quit()
    return policies


def generate_policy(insurer, url):
    return {
        "insurer": insurer,
        "policy_name": f"{insurer} Policy",
        "url": url,
        "monthly_premium": random.randint(500, 3000),
        "sum_assured": random.choice([25_00_000, 50_00_000, 1_00_00_000]),
        "claim_settlement_ratio": round(random.uniform(0.85, 0.99), 2),
        "policy_term_years": random.choice([20, 25, 30]),
        "premium_payment_term": random.choice([10, 15, 20]),
        "insurer_rating": round(random.uniform(3.8, 5.0), 1),
        "scraped_analysis": "Scraped Analysis High trust insurer with strong claim settlement record"
    }


if __name__ == "__main__":
    for insurer in INSURER_PAGES:
        print(f"\n--- {insurer.upper()} ---")
        data = scrape_insurer(insurer)
        for d in data:
>>>>>>> ffe7a5f (feat(ml): ml model to rank)
            print(d)