# File: src/extractors/table.py

"""Extractor for HTML table-based parish listings"""

import re
from typing import List, Optional
from bs4 import BeautifulSoup
from selenium import webdriver

from .base import BaseExtractor
from ..models import Parish

class TableExtractor(BaseExtractor):
    """Extract parishes from HTML tables"""
    
    def extract(self, soup: BeautifulSoup, url: str, driver: webdriver.Chrome = None) -> List[Parish]:
        """Extract parishes from table-based layout"""
        parishes = []
        tables = soup.find_all('table')
        
        for table in tables:
            # Check if table contains parish information
            table_text = table.get_text().lower()
            if not any(keyword in table_text for keyword in ['parish', 'church', 'name']):
                continue
                
            table_parishes = self._extract_parishes_from_table(table)
            parishes.extend(table_parishes)
        
        return self.remove_duplicates(parishes)
    
    def _extract_parishes_from_table(self, table) -> List[Parish]:
        """Extract parishes from a single table"""
        parishes = []
        rows = table.find_all('tr')
        
        if not rows:
            return parishes
        
        # Skip header row
        data_rows = rows[1:] if len(rows) > 1 else rows
        print(f"    Processing table with {len(data_rows)} data rows")
        
        for row in data_rows:
            parish = self._extract_parish_from_row(row)
            if parish:
                parishes.append(parish)
        
        return parishes
    
    def _extract_parish_from_row(self, row) -> Optional[Parish]:
        """Extract parish data from a single table row"""
        cells = row.find_all(['td', 'th'])
        if len(cells) < 1:
            return None
            
        # First cell usually contains parish name
        name = self.clean_text(cells[0].get_text())
        if not self.validate_parish_name(name):
            return None
        
        # Extract additional info from other cells
        address = phone = city = website = None
        
        for cell in cells[1:]:
            cell_text = cell.get_text()
            
            # Check for phone number
            if not phone:
                phone = self.extract_phone(cell_text)
            
            # Check for address (contains numbers and street words)
            if not address and self._looks_like_address(cell_text):
                address = self.clean_text(cell_text)
            
            # Check for city (short text, no numbers, not an address)
            if not city and self._looks_like_city(cell_text):
                city = self.clean_text(cell_text)
            
            # Check for website
            if not website:
                link = cell.find('a', href=True)
                if link:
                    href = link.get('href')
                    if href.startswith('http'):
                        website = href
        
        return Parish(
            name=name,
            city=city,
            address=address,
            phone=phone,
            website=website,
            confidence=0.85,
            extraction_method="table"
        )
    
    def _looks_like_address(self, text: str) -> bool:
        """Check if text looks like a street address"""
        if not text or len(text.strip()) < 5:
            return False
        
        # Must contain numbers and street indicators
        has_numbers = re.search(r'\d+', text)
        has_street_words = re.search(
            r'\b(?:st|street|ave|avenue|rd|road|dr|drive|ln|lane|blvd|boulevard|way|circle|court|ct)\b', 
            text, re.I
        )
        
        return bool(has_numbers and has_street_words)
    
    def _looks_like_city(self, text: str) -> bool:
        """Check if text looks like a city name"""
        if not text:
            return False
        
        text = text.strip()
        
        # City characteristics: short, no numbers, not too long
        return (
            5 < len(text) < 30 and
            not re.search(r'\d', text) and
            not self._looks_like_address(text) and
            not any(word in text.lower() for word in ['http', 'www', '@', '.com'])
        )
