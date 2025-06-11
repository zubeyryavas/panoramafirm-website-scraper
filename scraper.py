from playwright.sync_api import sync_playwright, TimeoutError
import csv
import time

SELECTORS = {
    "company_list": "#company-list > li",
    "name_link": "div.row.border-bottom.company-top-content.pb-1 > div.col-8.col-sm-10 > h2 > a",
    "name_link_optional": "div.row.border-bottom.company-top-content.pb-1 > div > h2 > a",
    "phone_modal_title": "#phone-modal .modal-header.text-dark .modal-title.w-100.font-weight-bold.text-dark",
    "sections": "#sections",
}

def get_contact_detail_by_label(detail_page, label_text):
    try:
        label_elem = detail_page.query_selector(f'text="{label_text}"')
        if not label_elem:
            return None, None

        container = label_elem.evaluate_handle("el => el.closest('.row')")
        if container:
            value_elem = container.query_selector("a") or container.query_selector("div")
            if value_elem:
                return value_elem.inner_text().strip(), value_elem
    except Exception as e:
        print(f"⚠️ Error getting contact detail '{label_text}': {e}")
    return None, None

def scrape_company(detail_page, base_url, company, i):
    try:
        name_a = company.query_selector(SELECTORS["name_link"]) or company.query_selector(SELECTORS["name_link_optional"])
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

        detail_page.goto(detail_url, wait_until="load")
        detail_page.wait_for_selector(SELECTORS["sections"])

        # Phone
        phone, phone_el = get_contact_detail_by_label(detail_page, "Telefon")
        if phone_el:
            try:
                phone_el.scroll_into_view_if_needed()
                time.sleep(0.2)
                detail_page.evaluate("(el) => el.click()", phone_el)
                time.sleep(0.5)
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
            phone = "N/A"
            print(f"[{i}] ⚠️ No phone found")

        # Email
        email, _ = get_contact_detail_by_label(detail_page, "Email")
        email = email or "N/A"

        # Website
        website, website_el = get_contact_detail_by_label(detail_page, "Strona www")
        if website_el:
            href = website_el.get_attribute("href")
            website = href or website
        else:
            website = website or "N/A"

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
        seen_contacts = set()
        company_counter = 1

        for page_number in range(132, 133):  # You can increase this range
            listing_url = f"{base_url}/hotele/firmy,{page_number}.html"
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

        with open("hotels.csv", "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["Name", "Phone", "Email", "Website"])
            writer.writeheader()
            writer.writerows(data)

        print(f"✅ Scraped {len(data)} unique hotels from {page_number} page(s) and saved to hotels.csv")

if __name__ == "__main__":
    main()
