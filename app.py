import streamlit as st
import pandas as pd
import asyncio
import aiohttp
import os

# 1. Logic for processing
def extract_from_json(data):
    # ... (Keep your extraction logic exactly as provided before) ...
    if not data: return 0, 0, 0, 0, 0
    total_facing = sum(item.get("facings", 0) for store in data.get("stores", []) for item in store.get("kpis", {}).get("facing_count", []))
    links = [img.get("annotated_image_path") for store in data.get("stores", []) for img in store.get("images", []) if img.get("annotated_image_path")]
    annotated = ", ".join(links) if links else 0
    missing_sku = "YES" if any(not str(i.get("sku_id", "")).strip() for s in data.get("stores", []) for i in s.get("kpis", {}).get("facing_count", [])) else "NO"
    visit_number = next((str(s.get("visit_number", "")).strip() or 0 for s in data.get("stores", [])), 0)
    market_iso = data.get("market_iso") or 0
    return total_facing, annotated, missing_sku, visit_number, market_iso

async def fetch_and_process(session, url):
    if not str(url).startswith("http"): return (0, 0, 0, 0, 0)
    try:
        async with session.get(url, timeout=10) as response:
            return extract_from_json(await response.json()) if response.status == 200 else (0, 0, 0, 0, 0)
    except: return (0, 0, 0, 0, 0)

async def run_batch(urls):
    connector = aiohttp.TCPConnector(limit=100)
    async with aiohttp.ClientSession(connector=connector) as session:
        return await asyncio.gather(*(fetch_and_process(session, url) for url in urls))

# 2. Main Process
st.title("Big Data JSON Processor")
uploaded_file = st.file_uploader("Upload CSV/Excel", type=["csv", "xlsx"])

if uploaded_file and st.button("🚀 Start Massive Processing"):
    output_filename = "processed_results.csv"
    chunk_size = 5000  # Process 5k rows at a time
    
    # Use chunksize to avoid OOM
    reader = pd.read_csv(uploaded_file, chunksize=chunk_size) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file, chunksize=chunk_size)
    
    for i, chunk in enumerate(reader):
        urls = chunk["pushed_data"].fillna("").astype(str).tolist()
        results = asyncio.run(run_batch(urls))
        
        chunk["Facing_Count"] = [r[0] for r in results]
        chunk["Annotated_Image_Link"] = [r[1] for r in results]
        chunk["Missing_SKU_ID"] = [r[2] for r in results]
        chunk["visit_number"] = [r[3] for r in results]
        chunk["Market_ISO"] = [r[4] for r in results]
        
        # Append to CSV on disk (don't keep in RAM)
        mode = 'w' if i == 0 else 'a'
        header = True if i == 0 else False
        chunk.to_csv(output_filename, mode=mode, index=False, header=header)
        st.write(f"Processed batch {i+1}")

    st.success("Processing Complete!")
    with open(output_filename, "rb") as f:
        st.download_button("Download Full Result", f, output_filename)
