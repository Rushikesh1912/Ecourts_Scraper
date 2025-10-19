# streamlit_app.py
import streamlit as st
from datetime import datetime
import os
from scraper.ecourts_scraper import ECourtsScraper
from scraper.dcourts_scraper import DCourtsScraper

st.set_page_config(page_title="⚖️ eCourts Smart Cause List Downloader", layout="wide")
st.title("⚖️ eCourts Smart Cause List Downloader")

# ---------------- Inputs ----------------
state = st.text_input("Enter State Name", "Maharashtra")
district = st.text_input("Enter District Name", "Pune")
court_complex = st.text_input("Enter Court Complex Name", "Pune, Civil and Criminal Court")
date = st.date_input("Select Date", datetime.today())
headless = st.checkbox("Headless Browser (unchecked to see Chrome)", False)
manual_fill = st.checkbox("Allow manual popup filling if auto-fill fails", True)

run_btn = st.button("Fetch Live Cause List & Generate PDF")

# ---------------- Run Scraper ----------------
if run_btn:
    status = st.empty()
    status.info("🚀 Opening eCourts website and waiting for data...")
    try:
        # Initialize scraper
        e_scraper = ECourtsScraper(
            download_dir="downloads",
            try_launch_chrome=True
        )
        
        # Generate PDF/JSON/CSV
        result = e_scraper.generate_pdf_for_date(
            state=state,
            district=district,
            court_complex=court_complex,
            date_str=date.strftime("%Y-%m-%d"),
            allow_manual_fill=manual_fill
        )
        e_scraper.close()

        # ---------------- Display results ----------------
        data = result.get("data", [])
        if data:
            st.success(f"✅ Cause list fetched! {len(data)} rows found.")
            st.dataframe(data)

            # PDF download
            pdf_path = result.get("pdf")
            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label="Download PDF",
                        data=f,
                        file_name=os.path.basename(pdf_path),
                        mime="application/pdf"
                    )

            # CSV download
            csv_path = result.get("csv")
            if csv_path and os.path.exists(csv_path):
                with open(csv_path, "rb") as f:
                    st.download_button(
                        label="Download CSV",
                        data=f,
                        file_name=os.path.basename(csv_path),
                        mime="text/csv"
                    )

            # JSON download
            json_path = result.get("json")
            if json_path and os.path.exists(json_path):
                with open(json_path, "rb") as f:
                    st.download_button(
                        label="Download JSON",
                        data=f,
                        file_name=os.path.basename(json_path),
                        mime="application/json"
                    )
        else:
            st.warning("⚠️ No data fetched. Using fallback cause list PDF...")
            d_scraper = DCourtsScraper(download_dir="downloads")
            pdf_path, fallback_data = d_scraper.download_all_for_date(date.strftime("%Y-%m-%d"))
            st.dataframe(fallback_data)
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="Download Fallback PDF",
                    data=f,
                    file_name=os.path.basename(pdf_path),
                    mime="application/pdf"
                )

    except Exception as e:
        st.error(f"❌ Error during fetch: {e}")
