import streamlit as st
import pandas as pd
import asyncio
import aiohttp
from io import BytesIO

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------
st.set_page_config(page_title="BAT JSON Updater", layout="wide")
st.title("BAT JSON Report Updater")

# ---------------------------------------------------
# EXTRACTION LOGIC (Synchronous helper)
# ---------------------------------------------------
def extract_from_json(data):
    if not data: return 0, 0, 0, 0, 0
    
    # Extract Facing Count
    total_facing = sum(item.get("facings", 0) for store in data.get("stores", []) 
                       for item in store.get("kpis", {}).get("facing_count", []))
    
    # Extract Links
    links = [img.get("annotated_image_path") for store in data.get("stores", []) 
             for img in store.get("images", []) if img.get("annotated_image_path")]
    annotated = ", ".join(links) if links else 0
    
    # Missing SKU
    sku_found = False
    missing_sku = "NO"
    for store in data.get("stores", []):
        for item in store.get("kpis", {}).get("facing_count", []):
            sku_found = True
            if not str(item.get("sku_id", "")).strip():
                missing_sku = "YES"
    if not sku_found: missing_sku = 0
    
    # Visit Number & Market
    visit_number = next((str(s.get("visit_number", "")).strip() or 0 for s in data.get("stores", [])), 0)
    market_iso = data.get("market_iso") or 0
    
    return total_facing, annotated, missing_sku, visit_number, market_iso

# ---------------------------------------------------
# ASYNC FETCHING
# ---------------------------------------------------
async def fetch_url(session, url):
    if not str(url).startswith("http"): return (0, 0, 0, 0, 0)
    try:
        async with session.get(url, timeout=15) as response:
            if response.status == 200:
                return extract_from_json(await response.json())
    except: pass
    return (0, 0, 0, 0, 0)

async def process_all_urls(urls):
    connector = aiohttp.TCPConnector(limit=100) # Adjust based on server capacity
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_url(session, url) for url in urls]
        return await asyncio.gather(*tasks)

# ---------------------------------------------------
# MAIN APP
# ---------------------------------------------------
uploaded_files = st.file_uploader("Upload Excel Files", type=["xlsx"], accept_multiple_files=True)

if uploaded_files and st.button("🚀 Start Processing"):
    for uploaded_file in uploaded_files:
        df = pd.read_excel(uploaded_file)
        if "pushed_data" not in df.columns:
            st.error(f"'pushed_data' missing in {uploaded_file.name}")
            continue
            
        urls = df["pushed_data"].fillna("").astype(str).tolist()
        
        with st.spinner(f"Processing {len(urls)} rows..."):
            results = asyncio.run(process_all_urls(urls))
            
        df["Facing_Count"] = [r[0] for r in results]
        df["Annotated_Image_Link"] = [r[1] for r in results]
        df["Missing_SKU_ID"] = [r[2] for r in results]
        df["visit_number"] = [r[3] for r in results]
        df["Market_ISO"] = [r[4] for r in results]
        
        output = BytesIO()
        df.to_excel(output, index=False)
        st.download_button(f"📥 Download {uploaded_file.name}", output.getvalue(), f"updated_{uploaded_file.name}")
        st.success(f"Finished {uploaded_file.name}")
