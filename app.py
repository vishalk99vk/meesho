# streamlit_app.py

import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="BAT Output JSON Updater",
    layout="wide"
)

st.title("BAT Output JSON Report Updater")

st.write("""
Upload one or multiple BAT Excel files.

This app will:
- Process only 'Output JSONs Report' sheet
- Read JSON links from pushed_data column
- Extract Facing Count
- Extract Annotated Image Link
- Detect Missing SKU ID
- Keep all other sheets unchanged
- Generate updated Excel automatically
""")

# ---------------------------------------------------
# FILE UPLOADER
# ---------------------------------------------------

uploaded_files = st.file_uploader(
    "Upload Excel Files",
    type=["xlsx", "xlsm", "xls"],
    accept_multiple_files=True
)

TARGET_SHEET = "Output JSONs Report"

# ---------------------------------------------------
# FUNCTIONS
# ---------------------------------------------------

def fetch_json(url):

    try:

        response = requests.get(url, timeout=30)

        if response.status_code == 200:
            return response.json()

        return None

    except:
        return None


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

        if len(annotated_links) == 0:
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

        # sku_id parameter not present
        if not sku_found:
            return 0

        return "NO"

    except:
        return 0


# ---------------------------------------------------
# MAIN PROCESS
# ---------------------------------------------------

if uploaded_files:

    start_processing = st.button("Start Processing")

    if start_processing:

        for uploaded_file in uploaded_files:

            st.divider()

            st.subheader(f"Processing: {uploaded_file.name}")

            try:

                # Read all sheets
                excel_file = pd.ExcelFile(uploaded_file)

                sheet_names = excel_file.sheet_names

                # Check target sheet
                if TARGET_SHEET not in sheet_names:

                    st.error(
                        f"'{TARGET_SHEET}' sheet not found in {uploaded_file.name}"
                    )
                    continue

                # Store all sheets
                all_sheets = {}

                for sheet in sheet_names:

                    all_sheets[sheet] = pd.read_excel(
                        uploaded_file,
                        sheet_name=sheet
                    )

                # Process only target sheet
                df = all_sheets[TARGET_SHEET]

                # Check pushed_data column
                if "pushed_data" not in df.columns:

                    st.error(
                        f"'pushed_data' column not found in {TARGET_SHEET}"
                    )
                    continue

                facing_counts = []
                annotated_links = []
                missing_sku_status = []

                total_rows = len(df)

                progress_bar = st.progress(0)

                status_text = st.empty()

                # ---------------------------------------------------
                # PROCESS EACH ROW
                # ---------------------------------------------------

                for idx, row in df.iterrows():

                    status_text.text(
                        f"Processing Row {idx + 1} of {total_rows}"
                    )

                    url = str(row["pushed_data"]).strip()

                    facing = 0
                    annotated = 0
                    missing_sku = 0

                    if url.startswith("http"):

                        json_data = fetch_json(url)

                        if json_data:

                            facing = extract_facing_count(json_data)

                            annotated = extract_annotated_link(json_data)

                            missing_sku = check_missing_sku_id(json_data)

                    facing_counts.append(facing)
                    annotated_links.append(annotated)
                    missing_sku_status.append(missing_sku)

                    progress_bar.progress((idx + 1) / total_rows)

                # ---------------------------------------------------
                # ADD NEW COLUMNS
                # ---------------------------------------------------

                df["Facing_Count"] = facing_counts
                df["Annotated_Image_Link"] = annotated_links
                df["Missing_SKU_ID"] = missing_sku_status

                # Update processed sheet
                all_sheets[TARGET_SHEET] = df

                # ---------------------------------------------------
                # SAVE UPDATED FILE
                # ---------------------------------------------------

                output = BytesIO()

                with pd.ExcelWriter(output, engine="openpyxl") as writer:

                    for sheet_name, sheet_df in all_sheets.items():

                        sheet_df.to_excel(
                            writer,
                            sheet_name=sheet_name,
                            index=False
                        )

                output.seek(0)

                output_filename = f"updated_{uploaded_file.name}"

                st.success(f"Completed: {uploaded_file.name}")

                # Preview
                st.dataframe(df.head())

                # Download button
                st.download_button(
                    label=f"Download {output_filename}",
                    data=output,
                    file_name=output_filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            except Exception as e:

                st.error(
                    f"Error Processing {uploaded_file.name}: {str(e)}"
                )
