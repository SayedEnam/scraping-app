import sys
import random
import string
import time
from datetime import datetime
import pandas as pd
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit, QFileDialog, QTableWidget, QTableWidgetItem
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

import os
from PIL import Image

# Get the correct path to icon.png whether running as script or as .exe
base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
icon_path = os.path.join(base_path, "icon.png")

# Load the icon
try:
    img = Image.open(icon_path)
except FileNotFoundError:
    print(f"❌ Error: Cannot find {icon_path}")
    sys.exit(1)  # Exit if the file is missing



# ChromeDriver Path
chromedriver_path = r'C:\Windows\chromedriver\chromedriver.exe'

class ScraperApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Product Scraper")
        self.setGeometry(100, 100, 800, 600)
        layout = QVBoxLayout()
        
        self.status_label = QLabel("Status: Ready")
        layout.addWidget(self.status_label)
        
        self.start_button = QPushButton("Start Scraping")
        self.start_button.clicked.connect(self.start_scraping)
        layout.addWidget(self.start_button)
        
        self.result_table = QTableWidget()
        layout.addWidget(self.result_table)
        
        self.export_button = QPushButton("Export CSV")
        self.export_button.clicked.connect(self.export_csv)
        self.export_button.setEnabled(False)
        layout.addWidget(self.export_button)
        
        self.setLayout(layout)
        self.products_data = []

    def start_scraping(self):
        self.status_label.setText("Status: Scraping started...")
        
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.page_load_strategy = 'eager'
        driver = webdriver.Chrome(service=Service(chromedriver_path), options=options)
        
        url = "https://www.laptopengine.com/product-category/laptops-laptops-computers/"
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        
        def load_all_products():
            while True:
                try:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    load_more_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "electron-load-more")))
                    driver.execute_script("arguments[0].click();", load_more_button)
                    time.sleep(5)
                except Exception:
                    break
        
        load_all_products()
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        category_tag = soup.find('h2')
        category = category_tag.get_text(strip=True) if category_tag else 'No category'
        product_items = soup.find_all('div', class_='electron-loop-product')
        
        self.products_data = []
        for product in product_items:
            title_tag = product.find('h6', class_='product-name')
            link_tag = title_tag.find('a') if title_tag else None
            product_link = link_tag['href'] if link_tag and link_tag.has_attr('href') else 'No link'
            title = link_tag.get_text(strip=True) if link_tag else 'No title'
            price_tag = product.find('span', class_='price-item--sale')
            price = price_tag.text.strip() if price_tag else 'No price'
            
            self.products_data.append([category, title, price, product_link])
        
        driver.quit()
        
        self.populate_table()
        self.status_label.setText("Status: Scraping completed!")
        self.export_button.setEnabled(True)
        
    def populate_table(self):
        self.result_table.setColumnCount(4)
        self.result_table.setRowCount(len(self.products_data))
        self.result_table.setHorizontalHeaderLabels(["Category", "Title", "Price", "Link"])
        
        for row, data in enumerate(self.products_data):
            for col, value in enumerate(data):
                self.result_table.setItem(row, col, QTableWidgetItem(value))
        
    def export_csv(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if filename:
            df = pd.DataFrame(self.products_data, columns=["Category", "Title", "Price", "Link"])
            df.to_csv(filename, index=False)
            self.status_label.setText(f"Status: Data exported to {filename}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScraperApp()
    window.show()
    sys.exit(app.exec())
