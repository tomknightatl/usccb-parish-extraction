# File: src/extractors/generic.py

"""Generic fallback extractor for unknown website layouts"""

from typing import List, Optional
from bs4 import BeautifulSoup
from selenium import webdriver

from .base import BaseExtractor
from ..models import Parish

class GenericExtractor(BaseExtractor):
    """Generic fallback extractor for unknown layouts"""
    
    def extract(self, soup: BeautifulSoup, url: str, driver: webdriver.Chrome = None) -> List[Parish]:
        """Generic extraction using common patterns"""
        parishes = []
        
        # Try multiple selectors for parish containers
        selectors = [
            "[class*='parish']",
            "[class*='church']", 
            "[class*='location']",
            "article",
            ".entry",
            "[id*='parish']",
            ".content-item",
            ".post"
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if not elements:
                continue
                
            print(f"    Trying generic extraction with {selector}: {len(elements)} elements")
            
            for elem in elements[:15]:  # Limit to prevent timeout
                parish = self._extract_parish_from_element(elem)
                if parish:
                    parishes.append(parish)
            
            # If we found some parishes, stop trying other selectors
            if parishes:
                break
        
        return self.remove_duplicates(parishes)
    
    def _extract_parish_from_element(self, elem) -> Optional[Parish]:
        """Extract parish data from a generic element"""
        # Look for parish name in headings
        name_elem = elem.find(['h1', 'h2', 'h3', 'h4', 'h5'])
        if not name_elem:
            return None
            
        name = self.clean_text(name_elem.get_text())
        if not self.validate_parish_name(name):
            return None
        
        # Extract other information from element text
        elem_text = elem.get_text()
        phone = self.extract_phone(elem_text)
        
        # Look for website links
        website = self._extract_website_from_element(elem)
        
        # Try to extract city from element structure
        city = self._extract_city_from_element(elem)
        
        # Look for address patterns
        address = self._extract_address_from_element(elem)
        
        return Parish(
            name=name,
            city=city,
            address=address,
            phone=phone,
            website=website,
            confidence=0.4,  # Lower confidence for generic extraction
            extraction_method="generic"
        )
    
    def _extract_website_from_element(self, elem) -> Optional[str]:
        """Extract website URL from element"""
        links = elem.find_all('a', href=True)
        for link in links:
            href = link.get('href')
            if (href.startswith('http') and 
                not any(skip in href.lower() for skip in ['facebook', 'twitter', 'instagram', 'youtube'])):
                return href
        return None
    
    def _extract_city_from_element(self, elem) -> Optional[str]:
        """Try to extract city from element structure"""
        # Look for address-like patterns
        text_lines = [line.strip() for line in elem.get_text().split('\n') if line.strip()]
        
        for line in text_lines[1:4]:  # Check first few lines after name
            if (len(line) < 30 and 
                not any(char in line for char in ['@', 'http', '(', ')']) and
                len(line.split()) <= 3):  # Cities are usually 1-3 words
                return self.clean_text(line)
        
        return None
    
    def _extract_address_from_element(self, elem) -> Optional[str]:
        """Try to extract address from element"""
        import re
        
        text_lines = [line.strip() for line in elem.get_text().split('\n') if line.strip()]
        
        for line in text_lines:
            # Look for address patterns
            if (re.search(r'\d+', line) and 
                re.search(r'\b(?:st|street|ave|avenue|rd|road|dr|drive)\b', line, re.I) and
                len(line) > 10):
                return self.clean_text(line)
        
        return None
