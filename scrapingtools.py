import os
import sys
import time
import random
import string
import pandas as pd
import re
from datetime import datetime

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QTextEdit, QLabel, QProgressBar
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup


# ✅ Scraper Worker Thread (Runs in Background)
class ScraperThread(QThread):
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url
        self.chromedriver_path = r'C:\Windows\chromedriver\chromedriver.exe'

    def run(self):
        self.log_signal.emit("Initializing browser...")
        
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.page_load_strategy = 'eager'

        driver = webdriver.Chrome(service=Service(self.chromedriver_path), options=options)
        driver.get(self.url)
        wait = WebDriverWait(driver, 10)

        # ✅ Load all products by clicking "Load More"
        def load_all_products():
            while True:
                try:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    load_more_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "electron-load-more")))
                    driver.execute_script("arguments[0].click();", load_more_button)
                    self.log_signal.emit("Clicked 'Load More'...")
                    time.sleep(5)
                except Exception:
                    self.log_signal.emit("All products loaded.")
                    break

        load_all_products()
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # ✅ Extract Category
        category_tag = soup.find('h2')
        category = category_tag.get_text(separator=" ", strip=True) if category_tag else 'No category'

        # ✅ Extract Products
        product_items = soup.find_all('div', class_='electron-loop-product')
        products_data = []
        total_products = len(product_items)
        self.log_signal.emit(f"Found {total_products} products.")

        def normalize_image_url(url):
            if url.startswith('//'):
                return f'https:{url}'
            elif url.startswith('http://'):
                return url.replace('http://', 'https://')
            elif not url.startswith(('http://', 'https://')):
                return f'https://{url}'
            return url

        def is_valid_image_url(url):
            return bool(re.match(r'^(https?://)', url))

        for i, product in enumerate(product_items):
            title_tag = product.find('h6', class_='product-name')
            link_tag = title_tag.find('a') if title_tag else None

            product_link = link_tag['href'] if link_tag and link_tag.has_attr('href') else 'No link'
            title = link_tag.get_text(strip=True) if link_tag else 'No title'
            price_tag = product.find('span', class_='price-item--sale')
            price = price_tag.text.strip() if price_tag else 'No price'

            if product_link.startswith("/"):
                product_link = f"https://www.laptopengine.com{product_link}"
            elif not product_link.startswith("http"):
                product_link = "No link available"

            if product_link != 'No link available':
                try:
                    driver.set_page_load_timeout(10)
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
                    description = desc_tag.get_text(separator="\n", strip=True) if desc_tag else 'No description'
                except Exception:
                    slider_images = ['No image']
                    description = 'No description'

            else:
                slider_images = ['No image']
                description = 'No description'

            products_data.append({
                'Category': category,
                'Name': title,
                'Images': ", ".join(slider_images),
                'Description': description,
                'Scraped': 'Yes',
            })

            self.progress_signal.emit(int((i + 1) / total_products * 100))

        driver.quit()

        # ✅ Export Data
        df = pd.DataFrame(products_data)
        filename = f"product_list_{datetime.now().strftime('%Y-%m-%d')}.csv"
        df.to_csv(filename, index=False)
        self.finished_signal.emit(f"✅ Data saved as {filename}")


# ✅ GUI Application
class ScraperApp(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Laptop Scraper")
        self.setGeometry(100, 100, 600, 400)
        
        # Load App Icon
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_path, "icon.ico")
        self.setWindowIcon(QIcon(icon_path))

        # UI Elements
        layout = QVBoxLayout()

        self.url_input = QLineEdit(self)
        self.url_input.setPlaceholderText("Enter website URL...")
        layout.addWidget(self.url_input)

        self.scrape_button = QPushButton("Start Scraping", self)
        self.scrape_button.clicked.connect(self.start_scraping)
        layout.addWidget(self.scrape_button)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.log_output = QTextEdit(self)
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        self.setLayout(layout)

    def start_scraping(self):
        url = self.url_input.text().strip()
        if not url:
            self.log_output.append("❌ Please enter a valid URL.")
            return

        self.log_output.append(f"🔍 Scraping: {url}")
        self.scraper_thread = ScraperThread(url)
        self.scraper_thread.progress_signal.connect(self.progress_bar.setValue)
        self.scraper_thread.log_signal.connect(self.log_output.append)
        self.scraper_thread.finished_signal.connect(lambda msg: self.log_output.append(msg))
        self.scraper_thread.start()


# ✅ Run Application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScraperApp()
    window.show()
    sys.exit(app.exec())
