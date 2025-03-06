import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# URL of the main listing page
url = "https://revibe.me/collections/refurbished-iphones-uae"

# Custom headers to mimic a real browser
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Send a GET request to the main listing page
try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
except requests.exceptions.RequestException as e:
    print(f"Failed to retrieve the main page: {e}")
    exit()

# List to store the extracted data
products_data = []

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(response.content, 'html.parser')

# Extract category from the <h2> tag
category_tag = soup.find('h2')
category = category_tag.get_text(separator=" ", strip=True) if category_tag else 'No category available'

# Find all product items
product_items = soup.find_all('div', class_='product-item')

# Loop through each product item and extract details
for product in product_items:
    # Extract product link
    link_tag = product.find('a', class_='card-title')
    product_link = f"https://revibe.me{link_tag['href']}" if link_tag and link_tag.has_attr('href') else 'No link available'

    # Extract product image
    image_tag = product.find('img', class_='motion-reduce')
    if image_tag:
        image_url = image_tag.get('data-srcset', '').split(',')[0].strip().split(' ')[0] if 'data-srcset' in image_tag.attrs else image_tag.get('src', 'No image available')
    else:
        image_url = 'No image available'

    # Extract product title
    title = link_tag.text.strip() if link_tag else 'No title available'

    # Extract product price
    price_tag = product.find('span', class_='price-item--sale')
    price = price_tag.text.strip() if price_tag else 'No price available'

    # Scrape product description from individual product page
    description = "No description available"
    if product_link != 'No link available':
        try:
            product_response = requests.get(product_link, headers=headers)
            product_response.raise_for_status()
            product_soup = BeautifulSoup(product_response.content, 'html.parser')
            desc_tag = product_soup.find('div', id='tab-technical-specifications')
            if desc_tag:
                description = desc_tag.get_text(separator="\n", strip=True)
        except requests.exceptions.RequestException:
            print(f"Failed to retrieve details for {title}")

    # Append the extracted details to the list, including category
    products_data.append({
        'Category': category,
        'Title': title,
        'Image URL': image_url,
        'Price': price,
        'Description': description,
        'Product Link': product_link
    })

    # To prevent overloading the server, sleep for a short time
    time.sleep(2)  # Increased delay to be gentler on the server

# Convert the list of dictionaries to a DataFrame
df = pd.DataFrame(products_data)

# Export the DataFrame to an Excel file
excel_filename = 'refurbished_iphones_with_descriptions.xlsx'
df.to_excel(excel_filename, index=False)

print(f"Data has been exported to {excel_filename}")
