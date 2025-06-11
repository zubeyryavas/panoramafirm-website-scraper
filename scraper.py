from playwright.sync_api import sync_playwright
import csv
import time

BASE_URL = "https://panoramafirm.pl"
LISTING_BASE_URL = BASE_URL + "/salony_spa_i_odnowa_biologiczna/firmy,"

SELECTORS = {
    "company_cards": "#company-list > li",
    "name_link": "div.row.border-bottom.company-top-content.pb-1 > div.col-8.col-sm-10 > h2 > a",
    "name_link_optional": "div.row.border-bottom.company-top-content.pb-1 > div > h2 > a",
    "inline_phone": "div:nth-child(1) > a.icon-telephone",
    "inline_website": "div:nth-child(2) > a.icon-website",
    "inline_email": "div:nth-child(3) > a.icon-envelope"
}

def extract_inline_details(company):
    phone_el = company.query_selector(SELECTORS["inline_phone"])
    phone = phone_el.get_attribute("data-original-title").strip() if phone_el and phone_el.get_attribute("data-original-title") else "N/A"

    website_el = company.query_selector(SELECTORS["inline_website"])
    website = website_el.get_attribute("href").strip() if website_el and website_el.get_attribute("href") else "N/A"

    email_el = company.query_selector(SELECTORS["inline_email"])
    email = email_el.get_attribute("data-company-email").strip() if email_el and email_el.get_attribute("data-company-email") else "N/A"

    return phone, email, website


def get_name_and_link(company):
    name_a = company.query_selector(SELECTORS["name_link"]) or company.query_selector(SELECTORS["name_link_optional"])
    if not name_a:
        return None, None
    name = name_a.inner_text().strip()
    link = name_a.get_attribute("href")
    return name, link

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        data = []
        seen_contacts = set()

        max_pages = 192  # Change this to the number of pages you want

        for page_num in range(1, max_pages + 1):
            print(f"📄 Visiting page {page_num}")
            page.goto(f"{LISTING_BASE_URL}{page_num}.html", timeout=30000)
            page.wait_for_selector(SELECTORS["company_cards"])
            companies = page.query_selector_all(SELECTORS["company_cards"])

            for company in companies:
                name, link = get_name_and_link(company)
                if not name:
                    continue

                phone, email, website = extract_inline_details(company)
                contact_key = (email, phone)

                if contact_key not in seen_contacts:
                    data.append({
                        "Name": name,
                        "Phone": phone,
                        "Email": email,
                        "Website": website
                    })
                    seen_contacts.add(contact_key)
                else:
                    print(f"⚠️ Duplicate found, skipping: {contact_key}")

                time.sleep(0.1)

        browser.close()

        with open("spa_and_wellness.csv", "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["Name", "Phone", "Email", "Website"])
            writer.writeheader()
            writer.writerows(data)

        print(f"✅ Scraped {len(data)} spa and wellness saloons and saved to spa_and_wellness.csv")

if __name__ == "__main__":
    main()
