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
        return clean
