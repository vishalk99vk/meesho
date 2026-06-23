# streamlit_app.py

import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="BAT JSON Updater",
    layout="wide"
)

st.title("BAT JSON Report Updater")

st.write("""
Upload one or multiple Excel files.

The app will:
- Read JSON URLs from pushed_data column
- Extract Facing Count
- Extract Annotated Image Link
- Detect Missing SKU ID
- Extract Visit ID
- Extract Market ISO
- Download updated Excel
""")

# ---------------------------------------------------
# FILE UPLOAD
# ---------------------------------------------------

uploaded_files = st.file_uploader(
    "Upload Excel Files",
    type=["xlsx", "xlsm", "xls"],
    accept_multiple_files=True
)

# ---------------------------------------------------
# REQUEST SESSION
# ---------------------------------------------------

session = requests.Session()

adapter = requests.adapters.HTTPAdapter(
    pool_connections=100,
    pool_maxsize=100
)

session.mount("http://", adapter)
session.mount("https://", adapter)

# ---------------------------------------------------
# FUNCTIONS
# ---------------------------------------------------

def fetch_json(url):

    try:

        response = session.get(url, timeout=30)

        if response.status_code == 200:
            return response.json()

        return None

    except:
        return None


@lru_cache(maxsize=50000)
def cached_fetch_json(url):
    return fetch_json(url)


def extract_facing_count(data):

    try:

        total_facing = 0

        stores = data.get("stores", [])

        for store in stores:

            kpis = store.get("kpis", {})

            facing_data = kpis.get("facing_count", [])

            for item in facing_data:

                total_facing += item.get("facings", 0)

        return total_facing

    except:
        return 0


def extract_annotated_link(data):

    try:

        stores = data.get("stores", [])

        annotated_links = []

        for store in stores:

            images = store.get("images", [])

            for img in images:

                link = img.get("annotated_image_path")

                if link:
                    annotated_links.append(link)

        if not annotated_links:
            return 0

        return ", ".join(annotated_links)

    except:
        return 0


def check_missing_sku_id(data):

    try:

        stores = data.get("stores", [])

        sku_found = False

        for store in stores:

            kpis = store.get("kpis", {})

            facing_data = kpis.get("facing_count", [])

            for item in facing_data:

                sku_found = True

                sku_id = str(item.get("sku_id", "")).strip()

                if sku_id == "":
                    return "YES"

        if not sku_found:
            return 0

        return "NO"

    except:
        return 0


def extract_visit_id(data):

    try:

        stores = data.get("stores", [])

        for store in stores:

            visit_id = str(store.get("visit_number", "")).strip()

            if visit_id:
                return visit_id

        return 0

    except:
        return 0


def extract_market_iso(data):

    try:

        market_iso = data.get("market_iso")

        if market_iso:
            return market_iso

        return 0

    except:
        return 0


def process_url(url):

    facing = 0
    annotated = 0
    missing_sku = 0
    visit_id = 0
    market_iso = 0

    try:

        if not str(url).startswith("http"):
            return (
                facing,
                annotated,
                missing_sku,
                visit_id,
                market_iso
            )

        json_data = cached_fetch_json(url)

        if json_data:

            facing = extract_facing_count(json_data)
            annotated = extract_annotated_link(json_data)
            missing_sku = check_missing_sku_id(json_data)
            visit_id = extract_visit_id(json_data)
            market_iso = extract_market_iso(json_data)

    except:
        pass

    return (
        facing,
        annotated,
        missing_sku,
        visit_id,
        market_iso
    )

# ---------------------------------------------------
# MAIN PROCESS
# ---------------------------------------------------

if uploaded_files:

    st.success(f"{len(uploaded_files)} file(s) uploaded")

    if st.button("🚀 Start Processing"):

        for uploaded_file in uploaded_files:

            st.divider()

            st.subheader(f"Processing: {uploaded_file.name}")

            try:

                df = pd.read_excel(uploaded_file)

                if "pushed_data" not in df.columns:

                    st.error(
                        f"'pushed_data' column not found in {uploaded_file.name}"
                    )
                    continue

                urls = df["pushed_data"].fillna("").astype(str).tolist()

                total = len(urls)

                progress_bar = st.progress(0)

                status_text = st.empty()

                results = []

                with ThreadPoolExecutor(max_workers=20) as executor:

                    for i, result in enumerate(
                        executor.map(process_url, urls)
                    ):

                        results.append(result)

                        if i % 100 == 0:

                            status_text.text(
                                f"Processed {i+1:,} / {total:,}"
                            )

                            progress_bar.progress(
                                min((i + 1) / total, 1.0)
                            )

                # -------------------------------------
                # CREATE OUTPUT COLUMNS
                # -------------------------------------

                df["Facing_Count"] = [r[0] for r in results]
                df["Annotated_Image_Link"] = [r[1] for r in results]
                df["Missing_SKU_ID"] = [r[2] for r in results]
                df["Visit_ID"] = [r[3] for r in results]
                df["Market_ISO"] = [r[4] for r in results]

                # -------------------------------------
                # SAVE FILE
                # -------------------------------------

                output = BytesIO()

                with pd.ExcelWriter(
                    output,
                    engine="openpyxl"
                ) as writer:

                    df.to_excel(
                        writer,
                        index=False
                    )

                output.seek(0)

                output_filename = (
                    f"updated_{uploaded_file.name}"
                )

                st.success(
                    f"Completed: {uploaded_file.name}"
                )

                st.dataframe(
                    df.head(),
                    use_container_width=True
                )

                st.download_button(
                    label=f"📥 Download {output_filename}",
                    data=output,
                    file_name=output_filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            except Exception as e:

                st.error(
                    f"Error processing {uploaded_file.name}: {str(e)}"
                )
