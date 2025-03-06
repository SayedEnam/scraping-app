import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from datetime import datetime
import random
import string

# Path to ChromeDriver
chromedriver_path = r'C:\Windows\chromedriver\chromedriver.exe'

# Set up Selenium options
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

# Initialize the browser
driver = webdriver.Chrome(service=Service(chromedriver_path), options=options)

# Open the target URL
url = "https://www.laptopengine.com/product-category/laptops-laptops-computers"
driver.get(url)

# Scroll down to load all products
last_height = driver.execute_script("return document.body.scrollHeight")
while True:
    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
    time.sleep(2)  # Wait for new content to load
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height

# Once all products are loaded, get the page source
soup = BeautifulSoup(driver.page_source, 'html.parser')

# Extract category
category_tag = soup.find('h2')
category = category_tag.get_text(separator=" ", strip=True) if category_tag else 'No category available'

# Find all product items
product_items = soup.find_all('div', class_='electron-loop-product')

# List to store extracted data
products_data = []

# Function to normalize image URLs to HTTPS
def normalize_image_url(url):
    if url.startswith('//'):
        return f'https:{url}'  # Convert protocol-relative URLs to HTTPS
    elif url.startswith('http://'):
        return url.replace('http://', 'https://')  # Convert HTTP to HTTPS
    elif not url.startswith(('http://', 'https://')):
        return f'https://{url}'  # Add HTTPS if the URL is missing a protocol
    return url  # Return as-is if already HTTPS

# Function to check if an image URL is valid (not base64)
def is_valid_image_url(url):
    return bool(re.match(r'^(https?://)', url))  # Only allow HTTP/HTTPS links

# Loop through each product item and extract details
for product in product_items:
    # Extract product title and link
    title_tag = product.find('h6', class_='product-name')
    link_tag = title_tag.find('a') if title_tag else None

    # Extract product link
    product_link = link_tag['href'] if link_tag and link_tag.has_attr('href') else 'No link available'

    # Extract product title
    title = link_tag.get_text(strip=True) if link_tag else 'No title available'

    # Extract product price
    price_tag = product.find('span', class_='price-item--sale')
    price = price_tag.text.strip() if price_tag else 'No price available'

    # Visit the product page to scrape full-size images
    if product_link != 'No link available':
        driver.get(product_link)
        time.sleep(3)  # Wait for the page to load
        
        # Scroll down to load all images
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        # Get the product page source
        product_soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Extract all slider images
        slider_images = []
        slider_divs = product_soup.find_all('div', class_='swiper-slide')
        for slider_div in slider_divs:
            img_tag = slider_div.find('img')
            if img_tag and img_tag.has_attr('src'):
                image_url = img_tag['src']
                if is_valid_image_url(image_url):  # Only add valid URLs
                    slider_images.append(normalize_image_url(image_url))

        # Extract product description
        desc_tag = product_soup.find('div', class_='name')
        description = desc_tag.get_text(separator="\n", strip=True) if desc_tag else 'No description available'
    else:
        slider_images = ['No image available']
        description = 'No description available'

    # Append extracted data to the list
    products_data.append({
        'Categories': category,
        'Name': title,
        'Images': ", ".join(slider_images) if slider_images else 'No valid images',  # Store images
        'Description': description,
    })

# Close the browser
driver.quit()

# Convert the list of dictionaries to a DataFrame
df = pd.DataFrame(products_data)

# Generate CSV filename
current_date = datetime.now().strftime('%Y-%m-%d')
random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
csv_filename = f'product_list_{current_date}_{random_string}.csv'

# Export DataFrame to CSV
df.to_csv(csv_filename, index=False)

print(f"Data has been exported to {csv_filename}")
