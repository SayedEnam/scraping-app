import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import pandas as pd
import time
import os


def scrape_revibe_products():
    # Set up Selenium
    chromedriver_path = r'C:\Windows\chromedriver\chromedriver.exe'
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode for server environments
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(chromedriver_path), options=options)
    url = "https://revibe.me/collections/refurbished-iphones-uae"
    driver.get(url)

    # Scroll to load all products
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    # Extract category
    category_tag = soup.find('h2')
    category = category_tag.get_text(separator=" ", strip=True) if category_tag else 'No category available'

    # Extract product details
    product_items = soup.find_all('div', class_='product-item')
    products_data = []

    for product in product_items:
        link_tag = product.find('a', class_='card-title')
        product_link = f"https://revibe.me{link_tag['href']}" if link_tag else 'No link available'
        image_tag = product.find('img', class_='motion-reduce')
        image_url = image_tag.get('data-srcset', '').split(',')[0].strip().split(' ')[0] if image_tag else 'No image available'
        title = link_tag.text.strip() if link_tag else 'No title available'
        price_tag = product.find('span', class_='price-item--sale')
        price = price_tag.text.strip() if price_tag else 'No price available'

        # Scrape product description from product page
        description = "No description available"
        if product_link != 'No link available':
            try:
                product_response = requests.get(product_link)
                product_response.raise_for_status()
                product_soup = BeautifulSoup(product_response.content, 'html.parser')
                desc_tag = product_soup.find('div', id='tab-technical-specifications')
                if desc_tag:
                    description = desc_tag.get_text(separator="\n", strip=True)
            except requests.exceptions.RequestException:
                print(f"Failed to retrieve details for {title}")

        products_data.append({
            'Category': category,
            'Title': title,
            'Image URL': image_url,
            'Price': price,
            'Description': description,
            'Product Link': product_link
        })

    # Save data to Excel
    df = pd.DataFrame(products_data)
    output_path = os.path.join(os.getcwd(), 'scraped_products.xlsx')
    df.to_excel(output_path, index=False)
    
    return output_path, products_data
