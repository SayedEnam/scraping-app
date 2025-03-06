import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
options.page_load_strategy = 'eager'  # Load pages faster

# Initialize the browser
driver = webdriver.Chrome(service=Service(chromedriver_path), options=options)

# Open the target URL
url = "https://www.laptopengine.com/product-category/laptops-laptops-computers/"
driver.get(url)

# Wait for elements to load
wait = WebDriverWait(driver, 10)

# Function to click "Load More" until all products are loaded
def load_all_products():
    while True:
        try:
            # Scroll to the bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            # Find the "Load More" button
            load_more_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "electron-load-more")))
            
            # Click the button
            driver.execute_script("arguments[0].click();", load_more_button)
            print("Clicked 'Load More' button...")
            
            # Wait for products to load
            time.sleep(5)

        except Exception:
            print("All products loaded or 'Load More' button not found.")
            break  # Exit when button disappears

# Call function to load all products
load_all_products()

# Get updated page source after loading all products
soup = BeautifulSoup(driver.page_source, 'html.parser')

# Extract category
category_tag = soup.find('h2')
category = category_tag.get_text(separator=" ", strip=True) if category_tag else 'No category available'

# Find all product items
product_items = soup.find_all('div', class_='electron-loop-product')

# List to store extracted data
products_data = []

# Function to normalize image URLs
def normalize_image_url(url):
    if url.startswith('//'):
        return f'https:{url}'
    elif url.startswith('http://'):
        return url.replace('http://', 'https://')
    elif not url.startswith(('http://', 'https://')):
        return f'https://{url}'
    return url

# Function to check valid image URL
def is_valid_image_url(url):
    return bool(re.match(r'^(https?://)', url))

# Loop through each product item and extract details
for product in product_items:
    title_tag = product.find('h6', class_='product-name')
    link_tag = title_tag.find('a') if title_tag else None

    product_link = link_tag['href'] if link_tag and link_tag.has_attr('href') else 'No link available'
    title = link_tag.get_text(strip=True) if link_tag else 'No title available'

    price_tag = product.find('span', class_='price-item--sale')
    price = price_tag.text.strip() if price_tag else 'No price available'

    # ✅ Fix: Validate and clean product link
    if product_link.startswith("/"):
        product_link = f"https://www.laptopengine.com{product_link}"
    elif not product_link.startswith("http"):
        product_link = "No link available"

    # ✅ Fix: Handle timeout errors when opening product pages
    if product_link != 'No link available':
        try:
            driver.set_page_load_timeout(10)  # ⏳ Limit load time
            driver.get(product_link)
            time.sleep(2)

            product_soup = BeautifulSoup(driver.page_source, 'html.parser')

            slider_images = []
            slider_divs = product_soup.find_all('div', class_='swiper-slide')
            for slider_div in slider_divs:
                img_tag = slider_div.find('img')
                if img_tag and img_tag.has_attr('src'):
                    image_url = img_tag['src']
                    if is_valid_image_url(image_url):
                        slider_images.append(normalize_image_url(image_url))

            desc_tag = product_soup.find('div', class_='product-desc-content')
            description = desc_tag.get_text(separator="\n", strip=True) if desc_tag else 'No description available'

        except Exception as e:
            print(f"❌ Error loading {product_link}: {str(e)}")
            slider_images = ['No image available']
            description = 'No description available'

    else:
        slider_images = ['No image available']
        description = 'No description available'

    # Store extracted data
    products_data.append({
        'Categories': category,
        'Name': title,
        'Images': ", ".join(slider_images) if slider_images else 'No valid images',
        'Description': description,
        'Meta: _scrapped': 'Yes',
    })

# Close the browser
driver.quit()

# Convert to DataFrame
df = pd.DataFrame(products_data)

# Generate CSV filename
current_date = datetime.now().strftime('%Y-%m-%d')
random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
csv_filename = f'product_list_{current_date}_{random_string}.csv'

# Export CSV
df.to_csv(csv_filename, index=False)

print(f"✅ Data exported to {csv_filename}")
