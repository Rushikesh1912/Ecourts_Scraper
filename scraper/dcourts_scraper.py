# scraper/dcourts_scraper.py
import os
from .utils import generate_pdf, ensure_dir

class DCourtsScraper:
    def __init__(self, download_dir="downloads"):
        self.download_dir = download_dir
        ensure_dir(download_dir)

    def download_all_for_date(self, date_str):
        data = [{"serial": "1", "judge": "Hon. Judge A", "court": "Court 1", "case": "Case A vs B"}]
        pdf_path = os.path.join(self.download_dir, f"fallback_causelist_{date_str}.pdf")
        generate_pdf(data, pdf_path, title="Fallback Cause List")
        return pdf_path, data
