from playwright.sync_api import sync_playwright, TimeoutError
import csv
import time

SELECTORS = {
    "company_list": "#company-list > li",
    "name_link": "div.row.border-bottom.company-top-content.pb-1 > div.col-8.col-sm-10 > h2 > a",
    "cookie_banner": "#hs-eu-cookie-confirmation",
    "phone_link": "#contact > div.pb-2.section-content > div > div:nth-child(4) > div.col-lg-8.col-sm-7.align-self-center > a",
    "phone_modal_title": "#phone-modal .modal-header.text-dark .modal-title.w-100.font-weight-bold.text-dark",
    "email_link": "#contact > div.pb-2.section-content > div > div:nth-child(5) > div.col-lg-8.col-sm-7.align-self-center > a",
    "website_link": "#contact > div.pb-2.section-content > div > div:nth-child(3) > div.col-lg-8.col-sm-7.align-self-center > div > a",
    "sections": "#sections",
}


# phone-modal > div
def scrape_company(detail_page, base_url, company, i):
    try:
        name_a = company.query_selector(SELECTORS["name_link"])
        if not name_a:
            print(f"[{i}] No name/link found, skipping")
            return None

        name = name_a.inner_text().strip()
        link = name_a.get_attribute("href")
        if not link:
            print(f"[{i}] No href found for {name}, skipping")
            return None

        detail_url = link if link.startswith("http") else base_url + link
        print(f"[{i}] Scraping details for: {name} - {detail_url}")

        detail_page.goto(detail_url, wait_until="networkidle")
        detail_page.wait_for_selector(SELECTORS["sections"])

        # Remove cookie banner if it exists
        try:
            detail_page.wait_for_selector(SELECTORS["cookie_banner"], timeout=3000)
            detail_page.evaluate(f"document.querySelector('{SELECTORS['cookie_banner']}').remove()")
        except TimeoutError:
            print(f"[{i}] ⚠️ Cookie banner not present")

        # Phone
        phone = "N/A"
        phone_el = detail_page.query_selector(SELECTORS["phone_link"])
        if phone_el:
            phone_el.scroll_into_view_if_needed()
            time.sleep(0.2)
            try:
                detail_page.evaluate("(el) => el.click()", phone_el)
                time.sleep(0.5)  # Give time for modal to open

                detail_page.wait_for_selector(SELECTORS["phone_modal_title"], timeout=10000)
                full_phone_el = detail_page.query_selector(SELECTORS["phone_modal_title"])
                if full_phone_el:
                    full_number = full_phone_el.inner_text().strip()
                    if full_number:
                        phone = full_number
                    else:
                        print(f"[{i}] ⚠️ Modal opened but phone number is missing")
                else:
                    print(f"[{i}] ❌ Modal selector not found")

                detail_page.keyboard.press("Escape")
                time.sleep(0.3)
            except TimeoutError:
                print(f"[{i}] ⏱️ Timeout while waiting for full phone modal")
            except Exception as e:
                print(f"[{i}] ❌ Error clicking phone element: {e}")
        else:
            print(f"[{i}] ❌ Could not find phone <a> element")

        # Email
        email = "N/A"
        email_el = detail_page.query_selector(SELECTORS["email_link"])
        if email_el:
            email = email_el.inner_text().strip()

        # Website
        website = "N/A"
        website_el = detail_page.query_selector(SELECTORS["website_link"])
        if website_el:
            website = website_el.get_attribute("href") or website_el.inner_text().strip()

        return {
            "Name": name,
            "Phone": phone,
            "Email": email,
            "Website": website,
        }
    except Exception as e:
        print(f"[{i}] ❌ Error scraping company details: {e}")
        return None


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        detail_page = browser.new_page()
        base_url = "https://panoramafirm.pl"
        data = []
        seen_contacts = set()  # To track (email, phone) combinations
        company_counter = 1

        for page_number in range(1, 2):  # Pages 1 to 2
            listing_url = f"https://panoramafirm.pl/hotele/firmy,{page_number}.html"
            print(f"Scraping listing page {page_number}: {listing_url}")
            page.goto(listing_url)
            page.wait_for_selector(SELECTORS["company_list"])

            companies = page.query_selector_all(SELECTORS["company_list"])

            for company in companies:
                result = scrape_company(detail_page, base_url, company, company_counter)
                if result:
                    contact_key = (result["Email"], result["Phone"])
                    if contact_key not in seen_contacts:
                        data.append(result)
                        seen_contacts.add(contact_key)
                    else:
                        print(f"[{company_counter}] ⚠️ Duplicate found, skipping: {contact_key}")
                company_counter += 1
                page.wait_for_timeout(100)  # polite delay

        detail_page.close()
        browser.close()

        # Save to CSV
        with open("hotels.csv", "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["Name", "Phone", "Email", "Website"])
            writer.writeheader()
            writer.writerows(data)

        print(f"✅ Scraped {len(data)} unique hotels from {page_number} pages and saved to hotels.csv")


if __name__ == "__main__":
    main()
