# scraper/ecourts_scraper.py
import subprocess
import time
import os
import re
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from .utils import ensure_dir, generate_pdf, save_json, save_csv

DEFAULT_DEBUG_PORT = 9222
DEFAULT_USER_DATA_DIR = r"C:/chrome-debug-eCourts"

class ECourtsScraper:
    BASE_URL = "https://services.ecourts.gov.in/ecourtindia_v6/?p=cause_list/"

    def __init__(self,
                 download_dir="downloads",
                 chrome_path=None,
                 debug_port=DEFAULT_DEBUG_PORT,
                 user_data_dir=DEFAULT_USER_DATA_DIR,
                 try_launch_chrome=True):
        """
        chrome_path: optional explicit path to chrome.exe
        try_launch_chrome: if attach to debugger fails, attempt to launch chrome with debugging port
        """
        self.download_dir = download_dir
        ensure_dir(download_dir)
        self.debug_port = debug_port
        self.user_data_dir = user_data_dir
        self.chrome_path = chrome_path or self._guess_chrome_path()
        self.try_launch_chrome = try_launch_chrome
        self.driver = None
        self.wait = None
        self._ensure_driver_attached()

    def _guess_chrome_path(self):
        # common Windows locations
        candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        ]
        for p in candidates:
            if Path(p).exists():
                return p
        return None

    def _launch_chrome_debug(self):
        # Launch a visible Chrome with remote debugging
        if not self.chrome_path:
            raise RuntimeError("Chrome executable not found. Please provide chrome_path or install Chrome.")
        ensure_dir(self.user_data_dir)
        cmd = [
            self.chrome_path,
            f"--remote-debugging-port={self.debug_port}",
            f'--user-data-dir={self.user_data_dir}',
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions"
        ]
        # start detached process
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # give Chrome time to start and open debug socket
        time.sleep(2.5)

    def _ensure_driver_attached(self):
        """
        Attempt to attach to existing Chrome at localhost:debug_port (debuggerAddress)
        If fails and try_launch_chrome True, launch Chrome with debugging and attach.
        """
        options = Options()
        debugger_addr = f"127.0.0.1:{self.debug_port}"
        options.add_experimental_option("debuggerAddress", debugger_addr)
        # keep GUI visible
        options.add_argument("--start-maximized")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--remote-allow-origins=*")

        chromedriver_path = ChromeDriverManager().install()
        service = Service(chromedriver_path)

        try:
            # First try attach (assumes user already started Chrome with debug port)
            self.driver = webdriver.Chrome(service=service, options=options)
            self.wait = WebDriverWait(self.driver, 30)
            return
        except Exception as e:
            # try launching Chrome with debug and attach
            if self.try_launch_chrome:
                try:
                    self._launch_chrome_debug()
                    time.sleep(1.5)
                    self.driver = webdriver.Chrome(service=service, options=options)
                    self.wait = WebDriverWait(self.driver, 30)
                    return
                except Exception as e2:
                    raise RuntimeError(f"Failed to attach to Chrome debugger. errors: {e} | {e2}")
            else:
                raise RuntimeError(f"Failed to attach to Chrome debugger. error: {e}")

    # ---------- Navigation & popup handling ----------
    def open_page(self):
        self.driver.get(self.BASE_URL)

    def _find_and_select_option(self, select_elem, desired_text):
        """
        Helper: click option with matching visible text (case-insensitive substring)
        """
        desired_text = (desired_text or "").strip().lower()
        for opt in select_elem.find_elements(By.TAG_NAME, "option"):
            txt = opt.text.strip().lower()
            if desired_text and desired_text in txt:
                opt.click()
                return True
        return False

    def try_auto_fill_popup(self, state, district, court_complex, wait_for_options=True):
        """
        Try multiple fallback IDs to find state/district/court dropdowns.
        Return True if we clicked a proceed or auto-filled at least one field.
        """
        filled_any = False
        # list of possible IDs for state/dropdown
        state_ids = ["selState", "sess_state_code", "state", "sess_state", "sel_state", "statecode"]
        district_ids = ["selDistrict", "sess_dist_code", "dist", "sess_dist", "sel_district", "distcode"]
        complex_ids = ["selCourtComplex", "court_complex_code", "courtComplex", "selCourt", "court_complex"]

        # try each combination; we expect at least one valid select element exists
        for sid in state_ids:
            try:
                sel_state = self.wait.until(EC.presence_of_element_located((By.ID, sid)))
                # wrap with Select if it's a <select>
                try:
                    sel = Select(sel_state)
                except Exception:
                    sel = Select(self.driver.find_element(By.ID, sid))
                self._find_and_select_option(sel_state, state)
                filled_any = True
                break
            except Exception:
                continue

        for did in district_ids:
            try:
                sel_d = self.wait.until(EC.presence_of_element_located((By.ID, did)))
                self._find_and_select_option(sel_d, district)
                filled_any = True
                break
            except Exception:
                continue

        for cid in complex_ids:
            try:
                sel_c = self.wait.until(EC.presence_of_element_located((By.ID, cid)))
                self._find_and_select_option(sel_c, court_complex)
                filled_any = True
                break
            except Exception:
                continue

        # Attempt to click Proceed or Submit in the popup
        try:
            proceed_btn = self.driver.find_element(By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'proceed') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ok')]")
            proceed_btn.click()
        except Exception:
            # maybe popup closes automatically or manual click needed
            pass

        return filled_any

    def wait_for_table(self, timeout=30):
        """
        Wait until the result table appears in the page.
        Some pages use ID 'resultTable', others 'result', 'result_table', or contain <table>.
        """
        possible_table_selectors = [
            (By.ID, "resultTable"),
            (By.ID, "result_table"),
            (By.ID, "result"),
            (By.CSS_SELECTOR, "table#resultTable"),
            (By.XPATH, "//table[contains(@id,'result') or contains(@class,'result') or contains(@class,'cause')]"),
            (By.TAG_NAME, "table")
        ]
        end_time = time.time() + timeout
        while time.time() < end_time:
            for by, sel in possible_table_selectors:
                try:
                    elem = self.driver.find_element(by, sel) if by != By.XPATH else self.driver.find_element(By.XPATH, sel)
                    # ensure it has rows
                    try:
                        trs = elem.find_elements(By.TAG_NAME, "tr")
                        if len(trs) >= 1:
                            return elem
                    except Exception:
                        return elem
                except Exception:
                    continue
            time.sleep(1)
        raise TimeoutError("Timed out waiting for result table to appear.")

    # ---------- Scrape ----------
    def parse_table(self, table_elem):
        """
        Parse a Selenium table element into list of dicts.
        Tries header-based mapping if header row present, else uses common columns.
        """
        rows = table_elem.find_elements(By.TAG_NAME, "tr")
        data = []
        if not rows:
            return data

        # check header
        header_cells = rows[0].find_elements(By.TAG_NAME, "th")
        if not header_cells:
            header_cells = rows[0].find_elements(By.TAG_NAME, "td")

        headers = [h.text.strip() if h.text.strip() else f"col{i}" for i, h in enumerate(header_cells, 1)]

        for r in rows[1:]:
            cols = r.find_elements(By.TAG_NAME, "td")
            if not cols:
                continue
            rowd = {}
            for i, c in enumerate(cols):
                key = headers[i] if i < len(headers) else f"col{i+1}"
                rowd[key] = c.text.strip()
            data.append(rowd)
        return data

    def generate_pdf_for_date(self, state, district, court_complex, date_str, allow_manual_fill=True):
        """
        Full flow: open page, try auto-fill popup, optionally wait for manual fill, wait for table, parse and save PDF/JSON/CSV.
        Returns dict with paths and scraped data.
        """
        self.open_page()
        time.sleep(1.2)

        filled = False
        try:
            filled = self.try_auto_fill_popup(state, district, court_complex)
        except Exception:
            filled = False

        # If auto-fill didn't work and manual allowed, instruct user to fill the popup in Chrome
        if not filled and allow_manual_fill:
            # wait until user clicks proceed and table loads
            table_elem = None
            try:
                table_elem = self.wait_for_table(timeout=90)
            except TimeoutError:
                # allow one more try after short sleep
                time.sleep(2)
                try:
                    table_elem = self.wait_for_table(timeout=30)
                except TimeoutError:
                    table_elem = None
            if not table_elem:
                # no table found -> return empty result
                return {"pdf": None, "json": None, "csv": None, "data": []}

        else:
            # if auto-filled we still wait for table to appear
            try:
                table_elem = self.wait_for_table(timeout=30)
            except TimeoutError:
                return {"pdf": None, "json": None, "csv": None, "data": []}

        data = self.parse_table(table_elem)
        safe_state = re.sub(r'\W+', '_', state or "state")
        safe_dist = re.sub(r'\W+', '_', district or "dist")
        safe_complex = re.sub(r'\W+', '_', court_complex or "complex")
        fname_base = f"{safe_state}_{safe_dist}_{safe_complex}_{date_str}"
        pdf_path = os.path.join(self.download_dir, f"{fname_base}.pdf")
        json_path = os.path.join(self.download_dir, f"{fname_base}.json")
        csv_path = os.path.join(self.download_dir, f"{fname_base}.csv")

        generate_pdf(data, pdf_path, title=f"Cause List - {state} / {district} / {court_complex}")
        save_json(data, json_path)
        save_csv(data, csv_path)

        return {"pdf": pdf_path, "json": json_path, "csv": csv_path, "data": data}

    def close(self):
        try:
            if self.driver:
                self.driver.quit()
        except Exception:
            pass
