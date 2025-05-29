# File: src/extractors/base.py

"""Base extractor class for parish data extraction"""

from abc import ABC, abstractmethod
from typing import List
from bs4 import BeautifulSoup
from selenium import webdriver

from ..models import Parish
from ..utils.webdriver import clean_text, extract_phone

class BaseExtractor(ABC):
    """Base class for all parish extractors"""
    
    def __init__(self):
        self.name = self.__class__.__name__
    
    @abstractmethod
    def extract(self, soup: BeautifulSoup, url: str, driver: webdriver.Chrome = None) -> List[Parish]:
        """Extract parishes from the given page"""
        pass
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        return clean_text(text)
    
    def extract_phone(self, text: str) -> str:
        """Extract phone number from text"""
        return extract_phone(text)
    
    def validate_parish_name(self, name: str) -> bool:
        """Validate that a string looks like a valid parish name"""
        if not name or len(name.strip()) < 3:
            return False
        
        # Skip obvious non-parish entries
        skip_terms = [
            'contact', 'office', 'directory', 'finder', 'search', 'filter',
            'map', 'diocese', 'bishop', 'center', 'no parish registration'
        ]
        
        name_lower = name.lower()
        if any(term in name_lower for term in skip_terms):
            return False
        
        # Must contain parish-like words
        parish_indicators = [
            'parish', 'church', 'st.', 'saint', 'our lady', 'holy', 
            'cathedral', 'chapel', 'basilica', 'shrine'
        ]
        
        return any(indicator in name_lower for indicator in parish_indicators)
    
    def remove_duplicates(self, parishes: List[Parish]) -> List[Parish]:
        """Remove duplicate parishes based on name"""
        unique_parishes = []
        seen_names = set()
        
        for parish in parishes:
            name_key = parish.name.lower().strip()
            if name_key not in seen_names and self.validate_parish_name(parish.name):
                unique_parishes.append(parish)
                seen_names.add(name_key)
        
        return unique_parishes
