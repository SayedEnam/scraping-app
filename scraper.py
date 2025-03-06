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

# Path to your ChromeDriver
chromedriver_path = r'C:\Windows\chromedriver\chromedriver.exe'

# Set up Selenium options
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

# Initialize the browser
driver = webdriver.Chrome(service=Service(chromedriver_path), options=options)

# Open the target URL
url = "https://revibe.me/collections/dell-secondhand-renewed-laptop"
driver.get(url)

# Scroll down to load all products
last_height = driver.execute_script("return document.body.scrollHeight")

while True:
    # Scroll to the bottom
    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
    
    # Wait for new content to load
    time.sleep(2)
    
    # Calculate new scroll height and compare with last scroll height
    new_height = driver.execute_script("return document.body.scrollHeight")
    
    if new_height == last_height:
        break  # No more content to load
    last_height = new_height

# Once all products are loaded, get the page source
soup = BeautifulSoup(driver.page_source, 'html.parser')

# Close the browser
driver.quit()

# Extract category
category_tag = soup.find('h2')
category = category_tag.get_text(separator=" ", strip=True) if category_tag else 'No category available'

# Find all product items
product_items = soup.find_all('div', class_='product-item')

# List to store extracted data
products_data = []

# Loop through each product item and extract details
for product in product_items:
    # Extract product link
    link_tag = product.find('a', class_='card-title')
    product_link = f"https://revibe.me{link_tag['href']}" if link_tag and link_tag.has_attr('href') else 'No link available'

    # Extract product image
    image_tag = product.find('img', class_='motion-reduce')
    if image_tag:
        if 'data-srcset' in image_tag.attrs:
            image_url_raw = image_tag.get('data-srcset', '').split(',')[0].strip().split(' ')[0]
        else:
            image_url_raw = image_tag.get('src', 'No image available')

        # Ensure the URL starts with https
        if image_url_raw.startswith('//'):
            image_url = 'https:' + image_url_raw
        elif not image_url_raw.startswith('http'):
            image_url = 'https://' + image_url_raw
        else:
            image_url = image_url_raw
    else:
        image_url = 'No image available'



    # Extract product title
    title = link_tag.text.strip() if link_tag else 'No title available'

    # Extract product price
    price_tag = product.find('span', class_='price-item--sale')
    if price_tag:
        price_text = price_tag.text.strip()
        
        # Remove currency symbols and commas, and extract numeric part
        price_numeric = re.sub(r'[^\d.]', '', price_text)  # Keeps only digits and decimal point
        
        # Optionally convert to float or int if needed
        price = float(price_numeric) if '.' in price_numeric else int(price_numeric)
    else:
        price = 'No price available'

    # Scrape product description from individual product page
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

    # Append the extracted details to the list
    products_data.append({
        'Categories': category,
        'Name': title,
        'Images': image_url,
        'Regular price': price,
        'Description': description,
        # 'Product Link': product_link
    })

# Convert the list of dictionaries to a DataFrame
df = pd.DataFrame(products_data)

# Get the current date in YYYY-MM-DD format
current_date = datetime.now().strftime('%Y-%m-%d')

# Generate a random 6-character string
random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

# Create the CSV file name with the current date and random string
csv_filename = f'product_list_{current_date}_{random_string}.csv'

# Export the DataFrame to a CSV file
df.to_csv(csv_filename, index=False)

print(f"Data has been exported to {csv_filename}")
