from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import requests
import os

def scrape_meesho_product(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")

        html = page.content()
        soup = BeautifulSoup(html, "html.parser")

        try:
            title = soup.find("h1").text.strip()
        except:
            title = "No Title Found"

        try:
            price = soup.find("span", {"class": "ProductPrice__FinalPrice"}).text.strip()
        except:
            price = "No Price Found"

        try:
            img_tag = soup.find("img")
            img_url = img_tag.get("src")
            img_data = requests.get(img_url).content

            os.makedirs("meesho_images", exist_ok=True)
            img_path = os.path.join("meesho_images", "product.jpg")
            with open(img_path, "wb") as handler:
                handler.write(img_data)
        except:
            img_path = None

        browser.close()
        return {"title": title, "price": price, "image": img_path}
