from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import requests
import os

def scrape_meesho_product(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle")
            html = page.content()
            browser.close()

        soup = BeautifulSoup(html, "html.parser")
        title = soup.find("h1").get_text(strip=True) if soup.find("h1") else "No Title"
        price = soup.find("span").get_text(strip=True) if soup.find("span") else "No Price"
        image_url = soup.find("img")["src"] if soup.find("img") else ""

        return {"title": title, "price": price, "image_url": image_url}
    except Exception as e:
        print(f"Error scraping product: {e}")
        return None

def download_image(url):
    try:
        if not url:
            return None
        response = requests.get(url)
        if response.status_code == 200:
            os.makedirs("meesho_images", exist_ok=True)
            file_path = os.path.join("meesho_images", "product.jpg")
            with open(file_path, "wb") as f:
                f.write(response.content)
            return file_path
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None
