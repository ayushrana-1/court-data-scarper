import re
import time
from playwright.sync_api import sync_playwright

def scrape_case_info(case_type, case_number, case_year, headless=False):
    """
    Sirf case ki basic info scrape karta hai:
    - Case number + status
    - Petitioner vs Respondent
    - Next hearing date
    - Last hearing date
    - Court no (agar available ho)

    Returns dict ya None agar case nahi mila.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()

        try:
            page.goto("https://delhihighcourt.nic.in/app/get-case-type-status", timeout=60000)

            # Fill form inputs
            page.select_option('select[name="case_type"]', case_type)
            page.fill('input[name="case_number"]', case_number)
            page.select_option('select[name="case_year"]', case_year)

            # Captcha fill
            captcha_value = page.inner_text('#captcha-code').strip()
            page.fill('#captchaInput', captcha_value)

            # Submit
            page.locator('#search').click()

            # Wait for table to appear (case results)
            # Table row selector: adjust if site changes
            page.wait_for_selector('table tbody tr', timeout=8000)
            time.sleep(1)  # small buffer

            # Check if any row exists
            rows = page.locator('table tbody tr')
            if rows.count() == 0:
                print("❌ No case row found.")
                return None

            first = rows.nth(0)
            cells = first.locator('td')
            if cells.count() < 4:
                print("❌ Unexpected table structure.")
                return None

            # Cell 1: S.No (ignore)
            # Cell 2: Diary No. / Case No. [STATUS]
            case_cell = cells.nth(1).inner_text().strip()
            # Extract case_no and status
            # Example: "CRL.A. - 1207 / 2019\n[DISPOSED]"
            case_no_match = re.search(r'([A-Za-z0-9\.\- ]+/\s*\d{4})', case_cell)
            status_match = re.search(r'\[([^\]]+)\]', case_cell)
            case_identifier = case_cell.split('\n')[0].strip()
            status = status_match.group(1).strip() if status_match else None

            # Cell 3: Petitioner Vs. Respondent
            parties = cells.nth(2).inner_text().strip()

            # Cell 4: Listing Date / Court No. block contains Next Date, Last Date, Court No
            date_block = cells.nth(3).inner_text().strip()

            # Parse dates using regex
            next_hearing = None
            last_hearing = None
            court_no = None

            # Example chunk: "NEXT DATE: NA\nLast Date: 23/01/2023\nCOURT NO:"
            nd = re.search(r'NEXT DATE:\s*([^\n]+)', date_block, re.IGNORECASE)
            if nd:
                next_hearing = nd.group(1).strip()

            ld = re.search(r'Last Date:\s*([^\n]+)', date_block, re.IGNORECASE)
            if ld:
                last_hearing = ld.group(1).strip()

            cn = re.search(r'COURT NO:\s*([^\n]*)', date_block, re.IGNORECASE)
            if cn:
                court_no = cn.group(1).strip() or None  # might be empty

            result = {
                "case_identifier": case_identifier,
                "status": status,
                "parties": parties,
                "next_hearing_date": next_hearing,
                "last_hearing_date": last_hearing,
                "court_no": court_no,
            }

            return result

        except Exception as e:
            print("Error scraping case info:", e)
            return None
        finally:
            browser.close()

# ---- Test run ----
if __name__ == "__main__":
    import sys
    # Set UTF-8 encoding for Windows
    if sys.platform.startswith('win'):
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    
    info = scrape_case_info("CRL.A.", "1207", "2019", headless=False)
    if info:
        print("\nScraped Info:")
        for k, v in info.items():
            print(f"{k}: {v}")
    else:
        print("Failed to get case info.")
