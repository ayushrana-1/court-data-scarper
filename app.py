import sqlite3
import sys
import os
from flask import Flask, render_template, request, jsonify
from project.info_scraper import scrape_case_info # Import the info scraper function
from project.backup_scraper import scrape_case_info_backup # Import backup scraper
from project.scarp import get_pdf_url # Import the PDF URL function

# Set UTF-8 encoding for Windows
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

app = Flask(__name__)
DATABASE = 'history.db' # Use relative path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape_case():
    case_type = request.form.get('case_type')
    case_number = request.form.get('case_number')
    case_year = request.form.get('case_year')

    if not case_type or not case_number or not case_year:
        return jsonify({"error": "Please fill in all fields."}), 400

    try:
        # First check if case already exists in database
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT status, parties, last_date, next_date, court_no FROM scrape_history WHERE case_type = ? AND case_number = ? AND case_year = ? AND status != 'Not Found' AND status NOT LIKE 'Error:%' ORDER BY rowid DESC LIMIT 1",
                       (case_type, case_number, case_year))
        existing_case = cursor.fetchone()
        
        if existing_case:
            # Case found in database, return cached data
            conn.close()
            case_info = {
                'case_identifier': f"{case_type} - {case_number} / {case_year}",
                'status': existing_case[0],
                'parties': existing_case[1],
                'last_hearing_date': existing_case[2],
                'next_hearing_date': existing_case[3],
                'court_no': existing_case[4],
                'pdf_link': None  # Will be fetched separately if needed
            }
            return jsonify({
                'success': True,
                'case_info': case_info,
                'from_cache': True  # Indicate this came from database
            })
        
        # Case not in database, scrape fresh data (both info and PDF)
        conn.close()  # Close connection before scraping
        
        print(f"Scraping fresh data for: {case_type} {case_number} {case_year}")
        
        case_info = None
        try:
            print(f"Attempting to scrape with info_scraper for: {case_type} {case_number} {case_year}")
            case_info = scrape_case_info(case_type, case_number, case_year, headless=True)
            print(f"Info scraper result: {case_info}")
            
            if not case_info:
                print("Info scraper returned None, trying backup scraper...")
                case_info = scrape_case_info_backup(case_type, case_number, case_year)
                print(f"Backup scraper result: {case_info}")
                
        except Exception as e:
            print(f"Scraping error: {str(e)}")
            print("Trying backup scraper...")
            try:
                case_info = scrape_case_info_backup(case_type, case_number, case_year)
                print(f"Backup scraper result: {case_info}")
            except Exception as backup_e:
                print(f"Backup scraper error: {str(backup_e)}")
                case_info = None
        
        # Also get PDF link if case info was found
        pdf_link = None
        if case_info:
            try:
                import time
                time.sleep(2)  # Small delay between scrapers
                pdf_link = get_pdf_url(case_type, case_number, case_year)
                print(f"PDF link result: {pdf_link}")
            except Exception as e:
                print(f"PDF scraping error: {e}")
                pdf_link = None
        
        # Reconnect to database to store results
        conn = get_db()
        cursor = conn.cursor()

        if case_info:
            # Insert fresh data into history (including PDF link)
            try:
                cursor.execute("INSERT INTO scrape_history (case_type, case_number, case_year, status, parties, last_date, next_date, court_no, pdf_link) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                               (case_type, case_number, case_year, case_info.get('status', 'N/A'), case_info.get('parties', 'N/A'), case_info.get('last_hearing_date', 'N/A'), case_info.get('next_hearing_date', 'N/A'), case_info.get('court_no', 'N/A'), pdf_link))
            except sqlite3.OperationalError:
                # Fallback for older database schema without pdf_link column
                cursor.execute("INSERT INTO scrape_history (case_type, case_number, case_year, status, parties, last_date, next_date, court_no) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                               (case_type, case_number, case_year, case_info.get('status', 'N/A'), case_info.get('parties', 'N/A'), case_info.get('last_hearing_date', 'N/A'), case_info.get('next_hearing_date', 'N/A'), case_info.get('court_no', 'N/A')))
            conn.commit()
            conn.close()
            # Add PDF link to case_info
            case_info['pdf_link'] = pdf_link
            return jsonify({
                'success': True,
                'case_info': case_info,
                'from_cache': False  # Indicate this was freshly scraped
            })
        else:
            # Handle cases where scraping was successful but no data found for the input
            cursor.execute("INSERT INTO scrape_history (case_type, case_number, case_year, status) VALUES (?, ?, ?, ?)",
                           (case_type, case_number, case_year, "Not Found"))
            conn.commit()
            conn.close()
            return jsonify({
                'success': False,
                'error': "No case found for the provided details."
            })
    except Exception as e:
        # Log the actual error for debugging
        error_msg = f"Error during scraping: {str(e)}"
        print(f"Main exception caught: {error_msg}")
        
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO scrape_history (case_type, case_number, case_year, status) VALUES (?, ?, ?, ?)",
                           (case_type, case_number, case_year, f"Error: {str(e)[:50]}"))
            conn.commit()
            conn.close()
        except Exception as db_e:
            print(f"Database error: {str(db_e)}")
            
        return jsonify({
            'success': False,
            'error': f"An error occurred: {str(e)}"
        })

@app.route('/get_pdf_url', methods=['POST'])
def get_pdf_link():
    case_type = request.form.get('case_type')
    case_number = request.form.get('case_number')
    case_year = request.form.get('case_year')

    if not case_type or not case_number or not case_year:
        return jsonify({"error": "Please provide case details."}), 400

    try:
        # Get PDF link from database first
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT pdf_link FROM scrape_history WHERE case_type = ? AND case_number = ? AND case_year = ? AND pdf_link IS NOT NULL ORDER BY rowid DESC LIMIT 1",
                       (case_type, case_number, case_year))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            return jsonify({
                'success': True,
                'pdf_url': result[0]
            })
        else:
            # If not in database, scrape fresh
            pdf_url = get_pdf_url(case_type, case_number, case_year)
            if pdf_url:
                return jsonify({
                    'success': True,
                    'pdf_url': pdf_url
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'No PDF found for this case.'
                })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Error retrieving PDF. Please try again.'
        })

@app.route('/test_pdf')
def test_pdf():
    """Test route to check PDF functionality"""
    try:
        pdf_url = get_pdf_url("CRL.A.", "1207", "2019")
        return jsonify({
            'success': True if pdf_url else False,
            'pdf_url': pdf_url,
            'message': 'PDF URL found' if pdf_url else 'No PDF found'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/history')
def history():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT case_type, case_number, case_year, status, parties, last_date, next_date, court_no, pdf_link FROM scrape_history ORDER BY rowid DESC")
    history_data = cursor.fetchall()
    conn.close()
    return jsonify(history_data)

def get_db():
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    # Create table with all columns
    cursor.execute("CREATE TABLE IF NOT EXISTS scrape_history (case_type TEXT, case_number TEXT, case_year TEXT, status TEXT, parties TEXT, last_date TEXT, next_date TEXT, court_no TEXT, pdf_link TEXT)")
    
    # Add pdf_link column if it doesn't exist (for existing databases)
    try:
        cursor.execute("ALTER TABLE scrape_history ADD COLUMN pdf_link TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    db.commit()
    return db

if __name__ == '__main__':
    app.run(debug=True)