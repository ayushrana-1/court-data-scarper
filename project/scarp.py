import time
import requests
from playwright.sync_api import sync_playwright

def fetch_case_and_download_pdf(case_type, case_number, case_year):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://delhihighcourt.nic.in/app/get-case-type-status")
        print("✅ Page opened")

        # Form fill
        page.select_option('select[name="case_type"]', case_type)
        page.fill('input[name="case_number"]', case_number)
        page.select_option('select[name="case_year"]', case_year)

        # Captcha get & fill
        captcha_value = page.inner_text('#captcha-code').strip()
        page.fill('#captchaInput', captcha_value)
        page.click('#search')

        time.sleep(3)

        # ✅ Click on "Orders" link
        orders_link = page.get_attribute('a:has-text("Orders")', 'href')
        if not orders_link:
            print("❌ No Orders link found.")
            browser.close()
            return

        print(f"📄 Orders page: {orders_link}")
        page.goto(orders_link)
        time.sleep(3)

        # ✅ Get all PDF links (they are <a href="...pdf">)
        page.wait_for_selector('a[href*=".pdf"]')  # ⏳ wait until PDF links load
        pdf_links = page.locator('//a[contains(@href, ".pdf")]')
        count = pdf_links.count()

        if count == 0:
            print("❌ No PDF orders found.")
            browser.close()
            return

        latest_pdf_url = pdf_links.nth(count - 1).get_attribute('href')
        full_pdf_url = latest_pdf_url#"https://delhihighcourt.nic.in" + latest_pdf_url

        print(f"✅ Latest Order PDF URL: {full_pdf_url}")
        browser.close()
        return full_pdf_url

    # ✅ Download PDF using requests
        # r = requests.get(full_pdf_url)
        # filename = f"order_{case_number}_{case_year}.pdf"
        # with open(filename, 'wb') as f:
        #     f.write(r.content)

        # print(f"📥 PDF downloaded as: {filename}")
        # browser.close()

def get_pdf_url(case_type, case_number, case_year):
    """
    Get PDF URL for a case without downloading
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            page.goto("https://delhihighcourt.nic.in/app/get-case-type-status")

            # Fill form inputs
            page.select_option('select[name="case_type"]', case_type)
            page.fill('input[name="case_number"]', case_number)
            page.select_option('select[name="case_year"]', case_year)

            # Captcha fill
            captcha_value = page.inner_text('#captcha-code').strip()
            page.fill('#captchaInput', captcha_value)
            page.click('#search')

            time.sleep(3)

            # Click on "Orders" link
            orders_link = page.get_attribute('a:has-text("Orders")', 'href')
            if not orders_link:
                browser.close()
                return None

            page.goto(orders_link)
            time.sleep(3)

            # Get all PDF links
            page.wait_for_selector('a[href*=".pdf"]')
            pdf_links = page.locator('//a[contains(@href, ".pdf")]')
            count = pdf_links.count()

            if count == 0:
                browser.close()
                return None

            latest_pdf_url = pdf_links.nth(count - 1).get_attribute('href')
            browser.close()
            return latest_pdf_url

        except Exception as e:
            browser.close()
            return None

# 🧪 Run test
# fetch_case_and_download_pdf(case_type="CRL.A.", case_number="1207", case_year="2019")
