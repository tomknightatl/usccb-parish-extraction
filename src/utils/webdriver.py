# File: src/utils/webdriver.py

"""WebDriver utilities for browser automation"""

import time
import re
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

def setup_driver() -> webdriver.Chrome:
    """Setup Chrome driver with optimal options for scraping"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")  # Speed up loading
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(5)
    return driver

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def load_page(driver: webdriver.Chrome, url: str) -> BeautifulSoup:
    """Load page with retry logic and return parsed HTML"""
    driver.get(url)
    time.sleep(2)  # Allow time for JavaScript to load
    return BeautifulSoup(driver.page_source, 'html.parser')

def clean_text(text: Optional[str]) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    return ' '.join(text.strip().split())

def extract_phone(text: Optional[str]) -> Optional[str]:
    """Extract phone number from text"""
    if not text:
        return None
    
    # Look for common phone patterns
    patterns = [
        r'\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})',  # (123) 456-7890 or 123-456-7890
        r'(\d{3})\.(\d{3})\.(\d{4})',  # 123.456.7890
        r'(\d{10})'  # 1234567890
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            if len(match.groups()) == 3:
                return f"({match.group(1)}) {match.group(2)}-{match.group(3)}"
            else:
                digits = match.group(1)
                return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    
    return None

def extract_coordinates(element) -> tuple[Optional[float], Optional[float]]:
    """Extract latitude and longitude from element attributes"""
    lat = element.get('data-latitude') or element.get('data-lat')
    lng = element.get('data-longitude') or element.get('data-lng') or element.get('data-lon')
    
    try:
        lat_float = float(lat) if lat and lat != '0.0' else None
        lng_float = float(lng) if lng and lng != '0.0' else None
        return lat_float, lng_float
    except (ValueError, TypeError):
        return None, None
