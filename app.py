import streamlit as st
from meesho_scraper import scrape_meesho_product
from facebook_poster import post_to_marketplace

st.title("Meesho to Facebook Marketplace")

product_link = st.text_input("Enter Meesho Product Link")
fb_email = st.text_input("Facebook Email")
fb_password = st.text_input("Facebook Password", type="password")

if st.button("Post to Marketplace"):
    if not product_link or not fb_email or not fb_password:
        st.warning("Please enter Meesho link and Facebook credentials.")
    else:
        with st.spinner("Scraping product..."):
            product = scrape_meesho_product(product_link)

        if product:
            st.image(product["image"], caption=product["title"])
            st.write(f"**Price:** {product['price']}")

            st.info("Posting to Facebook Marketplace...")
            result = post_to_marketplace(fb_email, fb_password, product)
            st.success(result)
        else:
            st.error("Failed to scrape product.")
