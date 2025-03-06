import os
import sys
import time
import pandas as pd
import re
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QTextEdit, QLabel,
    QProgressBar, QGridLayout, QMessageBox, QComboBox, QHBoxLayout
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup


# ✅ Scraper Worker Thread
class ScraperThread(QThread):
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)

    def __init__(self, url, selectors):
        super().__init__()
        self.url = url
        self.selectors = selectors
        self.chromedriver_path = r'C:\Windows\chromedriver\chromedriver.exe'

    def run(self):
        self.log_signal.emit("Initializing browser...")

        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.page_load_strategy = 'eager'

        driver = webdriver.Chrome(service=Service(self.chromedriver_path), options=options)
        driver.get(self.url)
        wait = WebDriverWait(driver, 10)

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # ✅ Extract Products
        product_items = soup.find_all(self.selectors["products_tag"], class_=self.selectors["products_class"])
        products_data = []
        total_products = len(product_items)
        self.log_signal.emit(f"Found {total_products} products.")

        for i, product in enumerate(product_items):
            title_tag = product.find(self.selectors["title_tag"], class_=self.selectors["title_class"])
            link_tag = title_tag.find('a') if title_tag else None

            product_link = link_tag['href'] if link_tag and link_tag.has_attr('href') else 'No link'
            title = link_tag.get_text(strip=True) if link_tag else 'No title'
            price_tag = product.find(self.selectors["price_tag"], class_=self.selectors["price_class"])
            price = price_tag.text.strip() if price_tag else 'No price'

            products_data.append({
                'Name': title,
                'Price': price,
                'Link': product_link,
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
        self.setWindowTitle("Scraper App v.10.0")
        self.setGeometry(100, 100, 600, 520)

        layout = QVBoxLayout()

        # ✅ URL Input
        self.url_input = QLineEdit(self)
        self.url_input.setPlaceholderText("Enter website URL...")
        layout.addWidget(QLabel("Website URL:"))
        layout.addWidget(self.url_input)

        # ✅ Grid Layout for Tags and Classes
        grid_layout = QGridLayout()

        # ✅ Dropdown options for HTML tags
        html_tags = ["div", "span", "h1", "h2", "h3", "h4", "h5", "h6", "a", "img", "p"]

        self.fields = {}
        fields_data = {
            "load_more": "Load More",
            "category": "Category",
            "products": "Products",
            "title": "Title",
            "price": "Price",
            "description": "Description",
            "image": "Image"
        }

        row = 0
        for key, label in fields_data.items():
            tag_dropdown = QComboBox(self)
            tag_dropdown.addItems(html_tags)

            class_input = QLineEdit(self)
            class_input.setPlaceholderText(f"Class for {label}")

            grid_layout.addWidget(QLabel(f"{label} Tag:"), row, 0)
            grid_layout.addWidget(tag_dropdown, row, 1)
            grid_layout.addWidget(QLabel("Class:"), row, 2)
            grid_layout.addWidget(class_input, row, 3)

            self.fields[key + "_tag"] = tag_dropdown
            self.fields[key + "_class"] = class_input
            row += 1

        layout.addLayout(grid_layout)

        self.scrape_button = QPushButton("Start Scraping", self)
        self.scrape_button.clicked.connect(self.start_scraping)
        layout.addWidget(self.scrape_button)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.log_output = QTextEdit(self)
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        # ✅ Footer Label
        footer_label = QLabel("Powered by Orbeen.com")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_label.setStyleSheet("color: gray; font-size: 12px; margin-top: 10px;")
        layout.addWidget(footer_label)

        self.setLayout(layout)

    def validate_inputs(self):
        if not self.url_input.text().strip():
            QMessageBox.warning(self, "Input Error", "Website URL cannot be empty.")
            return False
        return True

    def start_scraping(self):
        if not self.validate_inputs():
            return

        url = self.url_input.text().strip()
        selectors = {key: self.fields[key].currentText().strip() if "tag" in key else self.fields[key].text().strip() for key in self.fields}

        self.scraper_thread = ScraperThread(url, selectors)
        self.scraper_thread.log_signal.connect(self.log_output.append)
        self.scraper_thread.progress_signal.connect(self.progress_bar.setValue)
        self.scraper_thread.finished_signal.connect(lambda msg: self.log_output.append(msg))
        self.scraper_thread.start()


# ✅ Run Application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScraperApp()
    window.show()
    sys.exit(app.exec())
