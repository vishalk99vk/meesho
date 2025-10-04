import schedule
import time
from meesho_scraper import scrape_meesho_product, download_image
from facebook_poster import post_to_facebook

def daily_job(email, password, product_link):
    print(f"Running scheduled job for {product_link}")
    product_data = scrape_meesho_product(product_link)
    if product_data:
        product_data["image_path"] = download_image(product_data.get("image_url"))
        if product_data["image_path"]:
            post_to_facebook(email, password, product_data)

def start_scheduler(email, password, product_link, run_time="09:00"):
    schedule.every().day.at(run_time).do(daily_job, email=email, password=password, product_link=product_link)

    while True:
        schedule.run_pending()
        time.sleep(60)
