from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

def post_to_facebook(email, password, product_data):
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        driver.get("https://www.facebook.com/marketplace/create/item/")

        time.sleep(3)
        driver.find_element(By.ID, "email").send_keys(email)
        driver.find_element(By.ID, "pass").send_keys(password)
        driver.find_element(By.NAME, "login").click()

        time.sleep(5)

        driver.find_element(By.XPATH, "//input[@type='file']").send_keys(product_data["image_path"])
        driver.find_element(By.XPATH, "//input[@aria-label='Title']").send_keys(product_data["title"])
        driver.find_element(By.XPATH, "//input[@aria-label='Price']").send_keys(product_data["price"])
        driver.find_element(By.XPATH, "//textarea[@aria-label='Description']").send_keys(product_data["title"])

        time.sleep(2)
        driver.find_element(By.XPATH, "//button[text()='Post']").click()
        time.sleep(5)

        driver.quit()
        print("Posted successfully to Facebook Marketplace!")
    except Exception as e:
        print(f"Error posting to Facebook: {e}")
