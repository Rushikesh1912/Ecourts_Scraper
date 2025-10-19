# scraper/utils.py
import os
import json
import csv
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime

def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def save_json(data, out_path):
    ensure_dir(os.path.dirname(out_path))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return out_path

def save_csv(data_list, out_path):
    """
    Save a list of dicts to CSV.
    Handles dynamic/missing columns gracefully by using the union of all keys.
    """
    ensure_dir(os.path.dirname(out_path))
    if not data_list:
        return None

    # Get union of all keys
    all_keys = set()
    for row in data_list:
        all_keys.update(row.keys())
    keys = list(all_keys)

    # Normalize rows: fill missing keys with empty string
    normalized_rows = []
    for row in data_list:
        normalized_rows.append({k: row.get(k, "") for k in keys})

    with open(out_path, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(normalized_rows)
    return out_path

def generate_pdf(data_list, out_path, title="eCourts Cause List"):
    """
    Simple multi-page PDF generator using ReportLab.
    data_list: list of dicts
    """
    ensure_dir(os.path.dirname(out_path))
    c = canvas.Canvas(out_path, pagesize=A4)
    width, height = A4
    margin_x = 40
    y = height - 60

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2.0, y, title)
    y -= 24
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2.0, y, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 30

    if not data_list:
        c.setFont("Helvetica", 12)
        c.drawString(margin_x, y, "No data available.")
        c.save()
        return out_path

    # headers (use union of all keys)
    headers = set()
    for row in data_list:
        headers.update(row.keys())
    headers = list(headers)
    col_width = (width - 2 * margin_x) / len(headers)
    
    # draw headers
    c.setFont("Helvetica-Bold", 10)
    x = margin_x
    for h in headers:
        c.drawString(x, y, str(h).upper())
        x += col_width
    y -= 16
    c.setFont("Helvetica", 9)

    # draw rows
    for i, row in enumerate(data_list, 1):
        x = margin_x
        for h in headers:
            value = str(row.get(h, "")).replace("\n", " ")
            # wrap if too long
            max_chars = int(col_width // 6)
            if len(value) > max_chars:
                value = value[: max_chars - 3] + "..."
            c.drawString(x, y, value)
            x += col_width
        y -= 14
        if y < 60:
            c.showPage()
            y = height - 60
            # redraw headers
            c.setFont("Helvetica-Bold", 10)
            x = margin_x
            for h in headers:
                c.drawString(x, y, str(h).upper())
                x += col_width
            y -= 16
            c.setFont("Helvetica", 9)

    c.save()
    return out_path
