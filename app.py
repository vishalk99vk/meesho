import streamlit as st
from meesho_scraper import scrape_meesho_product

st.title("Meesho Product Scraper")

product_link = st.text_input("Enter Meesho product link:")

if st.button("Scrape"):
    if not product_link:
        st.warning("Please enter Meesho link.")
    else:
        with st.spinner("Scraping product..."):
            product = scrape_meesho_product(product_link)

        if product:
            st.image(product["image"], caption=product["title"])
        else:
            st.error("Failed to scrape product.")
