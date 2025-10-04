from playwright.sync_api import sync_playwright

def scrape_meesho_product(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        
        # Example: extract title and image
        title = page.title()
        image_element = page.query_selector("img")  # simple selector
        image_url = image_element.get_attribute("src") if image_element else None

        browser.close()
        return {"title": title, "image": image_url}
