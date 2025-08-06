# Delhi High Court Case Scraper

A Flask web application that scrapes case information from the Delhi High Court website. This tool allows users to search for court cases and retrieve detailed information including case status, parties involved, hearing dates, and PDF documents.

**Demo Video**: https://youtu.be/_wTNQZhE2z0

## Features

- 🔍 **Case Search**: Search for cases by type, number, and year
- 📊 **Case Information**: Get detailed case status, parties, and hearing dates
- 📄 **PDF Access**: Direct links to court order PDFs
- 🗄️ **History Tracking**: SQLite database stores search history for faster retrieval
- 🌐 **Web Interface**: Clean, user-friendly dashboard
- ⚡ **Caching**: Avoids redundant scraping by storing previous results

## Project Structure

```
p1/
├── app.py                 # Main Flask application
├── history.db            # SQLite database for search history
├── project/
│   ├── info_scraper.py   # Main web scraper using Playwright
│   └── scarp.py          # Alternative scraper for PDF downloads
├── templates/
│   └── index.html        # Frontend dashboard
├── static/
│   └── style.css         # Styling for the web interface
└── README.md             # This file
```

## Prerequisites

- Python 3.7 or higher
- Playwright browsers (for web scraping)

## Installation

1. **Clone or download the project**
   ```bash
   cd court-data-scarper
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment**
   - On Windows:
     ```bash
     .venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```

4. **Install required packages**
   ```bash
   pip install flask playwright
   ```

5. **Install Playwright browsers**
   ```bash
   playwright install
   ```

## Usage

### Starting the Application

1. **Run the Flask app**
   ```bash
   python app.py
   ```

2. **Open your web browser** and navigate to:
   ```
   http://localhost:5000
   ```

### Using the Web Interface

1. **Search for a Case**:
   - Select case type from dropdown (e.g., "CRL.A.", "W.P.(C)", etc.)
   - Enter case number (e.g., "1207")
   - Enter case year (e.g., "2019")
   - Click "Fetch Case Info"

2. **View Results**:
   - Case status and current stage
   - Parties involved in the case
   - Last hearing date
   - Next hearing date (if scheduled)
   - Court number

3. **Get PDF Documents**:
   - After searching for a case, click "Get PDF Link"
   - If available, a direct link to the court order PDF will be provided

4. **View Search History**:
   - Click "View History" to see all previous searches
   - Cached results load instantly without re-scraping

### API Endpoints

The application also provides REST API endpoints:

- `GET /` - Main dashboard
- `POST /scrape` - Search for case information
- `POST /get_pdf_url` - Get PDF link for a case
- `GET /history` - View search history
- `GET /test_pdf` - Test PDF functionality

### Example API Usage

```bash
# Search for a case
curl -X POST http://localhost:5000/scrape \
  -d "case_type=CRL.A.&case_number=1207&case_year=2019"

# Get PDF link
curl -X POST http://localhost:5000/get_pdf_url \
  -d "case_type=CRL.A.&case_number=1207&case_year=2019"
```

## How It Works

1. **Web Scraping**: Uses Playwright to automate browser interactions with the Delhi High Court website
2. **Data Extraction**: Parses HTML to extract case details like status, parties, and dates
3. **Caching**: Stores results in SQLite database to avoid repeated scraping
4. **PDF Retrieval**: Locates and provides direct links to court order PDFs
5. **Web Interface**: Flask serves a responsive dashboard for easy interaction

## Common Case Types

- `CRL.A.` - Criminal Appeal
- `W.P.(C)` - Writ Petition (Civil)
- `CRL.M.C.` - Criminal Miscellaneous Case
- `CRL.REV.P.` - Criminal Revision Petition
- `FAO` - First Appeal from Order
- `RFA` - Regular First Appeal

## Troubleshooting

### Browser Issues
If you encounter browser-related errors:
```bash
playwright install --force
```

### Database Issues
If the database gets corrupted, delete `history.db` and restart the app:
```bash
rm history.db
python app.py
```

### Case Not Found
- Verify the case type, number, and year are correct
- Some cases may not be available online
- Try different case type formats

## Important Notes

- **Legal Compliance**: This tool is for educational and research purposes
- **Rate Limiting**: The scraper includes delays to avoid overwhelming the court website
- **Data Accuracy**: Always verify information from official sources
- **Maintenance**: Court website changes may require scraper updates

## Contributing

Feel free to submit issues and enhancement requests. When contributing:

1. Test your changes thoroughly
2. Follow existing code style
3. Update documentation as needed
4. Ensure compatibility with the court website structure

## License

This project is for educational purposes. Please respect the Delhi High Court website's terms of service and use responsibly.

---

**Disclaimer**: This tool scrapes publicly available information from the Delhi High Court website. Users are responsible for complying with all applicable laws and the website's terms of service.
