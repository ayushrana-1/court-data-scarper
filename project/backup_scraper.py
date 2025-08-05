import requests
import re
from bs4 import BeautifulSoup
import time

def scrape_case_info_backup(case_type, case_number, case_year):
    """
    Backup scraper using requests instead of Playwright
    """
    try:
        session = requests.Session()
        
        # First get the main page to get session cookies
        url = "https://delhihighcourt.nic.in/app/get-case-type-status"
        response = session.get(url, timeout=30)
        
        if response.status_code != 200:
            print(f"Failed to load page: {response.status_code}")
            return None
            
        # Parse the page to get captcha
        soup = BeautifulSoup(response.text, 'html.parser')
        captcha_element = soup.find('span', {'id': 'captcha-code'})
        
        if not captcha_element:
            print("Captcha element not found")
            return None
            
        captcha_value = captcha_element.get_text().strip()
        print(f"Captcha value: {captcha_value}")
        
        # Prepare form data
        form_data = {
            'case_type': case_type,
            'case_number': case_number,
            'case_year': case_year,
            'captchaInput': captcha_value
        }
        
        # Submit the form
        response = session.post(url, data=form_data, timeout=30)
        
        if response.status_code != 200:
            print(f"Form submission failed: {response.status_code}")
            return None
            
        # Parse the results
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the results table
        table = soup.find('table')
        if not table:
            print("No results table found")
            return None
            
        rows = table.find_all('tr')
        if len(rows) < 2:  # Header + at least one data row
            print("No case data found")
            return None
            
        # Get the first data row (skip header)
        data_row = rows[1]
        cells = data_row.find_all('td')
        
        if len(cells) < 4:
            print("Incomplete case data")
            return None
            
        # Extract data from cells
        case_cell = cells[1].get_text().strip()
        parties = cells[2].get_text().strip()
        date_block = cells[3].get_text().strip()
        
        # Parse case number and status
        case_identifier = case_cell.split('\n')[0].strip()
        status_match = re.search(r'\[([^\]]+)\]', case_cell)
        status = status_match.group(1).strip() if status_match else None
        
        # Parse dates
        next_hearing = None
        last_hearing = None
        court_no = None
        
        nd = re.search(r'NEXT DATE:\s*([^\n]+)', date_block, re.IGNORECASE)
        if nd:
            next_hearing = nd.group(1).strip()
            
        ld = re.search(r'Last Date:\s*([^\n]+)', date_block, re.IGNORECASE)
        if ld:
            last_hearing = ld.group(1).strip()
            
        cn = re.search(r'COURT NO:\s*([^\n]*)', date_block, re.IGNORECASE)
        if cn:
            court_no = cn.group(1).strip() or None
            
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
        print(f"Backup scraper error: {e}")
        return None

if __name__ == "__main__":
    # Test the backup scraper
    result = scrape_case_info_backup("CRL.A.", "1207", "2019")
    if result:
        print("Backup scraper working!")
        for k, v in result.items():
            print(f"{k}: {v}")
    else:
        print("Backup scraper failed")
