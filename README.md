# ⚖️ eCourts Smart Cause List Scraper

A Python + Streamlit project to **automatically fetch cause lists from eCourts India** in real-time, and generate **PDF, CSV, and JSON reports**.  
The project handles dynamic tables, auto-fills popups, and supports manual intervention if required.

---

## Features

- Real-time scraping from [eCourts India](https://services.ecourts.gov.in/ecourtindia_v6/?p=cause_list/)
- Auto-fill State, District, and Court Complex in popup
- Manual input fallback if auto-fill fails
- Download reports in:
  - **PDF** (well-formatted, multi-page)
  - **CSV** (dynamic headers supported)
  - **JSON**
- Supports any number of columns in tables dynamically
- Streamlit interface for easy interaction
- Cross-platform compatible (Windows/Linux with Chrome)

---

## Installation

1. Clone the repository:

```bash
git clone <your-repo-url>
cd <repo-folder>

Create a virtual environment (recommended):
bash
Copy code
python -m venv venv
Activate the environment:

Windows:
bash
Copy code
venv\Scripts\activate

Linux/macOS:
bash
Copy code
source venv/bin/activate

Install dependencies:
bash
Copy code
pip install -r requirements.txt

Usage
Launch Chrome with remote debugging (optional but recommended for real-time scraping):
bash
Copy code
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:/chrome-debug"

Run Streamlit app:
bash
Copy code
streamlit run streamlit_app.py

Open the Streamlit interface in your browser:
Enter State, District, Court Complex, and Date.
Click Fetch Cause List & Generate PDF.
Download the generated PDF, CSV, or JSON file.

Project Structure
Copy code
├── scraper/
│   ├── utils.py
│   ├── ecourts_scraper.py
│   └── dcourts_scraper.py
├── streamlit_app.py
├── requirements.txt
└── README.md


How It Works
Browser Connection:
Connects to Chrome either in headless mode or via remote debugging port.
Popup Handling:
Automatically fills the State, District, and Court Complex dropdowns in the eCourts website popup.
Manual filling is supported if auto-fill fails.
Data Scraping:
Waits for the cause list table to appear and scrapes all rows dynamically.
Supports any number of columns (e.g., Sr No, Cases, Party Name, Advocate, etc.).
Report Generation:
PDF: Multi-page with headers, titles, and timestamp.
CSV: Dynamic headers matching table columns.
JSON: Full structured data.



## 🖼️ Sample Screenshots

### 🧪 Streamlit Interface  
![Streamlit Interface](https://raw.githubusercontent.com/Rushikesh1912/Ecourts_Scraper/main/Outputs/streamlit_ui.jpg)

### 📊 Fetched Cause List Table in Streamlit  
![Fetched Results](https://raw.githubusercontent.com/Rushikesh1912/Ecourts_Scraper/main/Outputs/fetched_results.jpg)

### 📄 Generated PDF Sample  
![Generated PDF](https://raw.githubusercontent.com/Rushikesh1912/Ecourts_Scraper/main/Outputs/sample_pdf.jpg)



Dependencies
Python 3.10+
Streamlit
Selenium
Webdriver Manager
ReportLab
Requests

All dependencies are listed in requirements.txt.



Notes
Make sure Google Chrome is installed.

Launching Chrome with the remote debugging port ensures full real-time scraping.
Manual popup filling is supported if auto-fill fails.
CSV generation dynamically adapts to table columns in the eCourts website.



License
MIT License © [Rushikesh Kadam]
Btech-Artificial intelligence and Data Science

Vishwakarma University, Pune













