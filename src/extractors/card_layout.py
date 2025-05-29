# File: src/extractors/card_layout.py

"""Extractor for card-based parish layouts"""

import re
from typing import List, Optional
from bs4 import BeautifulSoup
from selenium import webdriver

from .base import BaseExtractor
from ..models import Parish

class CardLayoutExtractor(BaseExtractor):
    """Extract parishes from card-based layouts (like Salt Lake City diocese)"""
    
    def extract(self, soup: BeautifulSoup, url: str, driver: webdriver.Chrome = None) -> List[Parish]:
        """Extract parishes from card layout page"""
        parishes = []
        
        # Look for different types of card layouts
        card_selectors = [
            'div.col-lg.location',  # Salt Lake City style
            '[class*="parish-card"]',
            '[class*="location-card"]', 
            '[class*="church-card"]',
            '.card'  # Generic card class
        ]
        
        cards = []
        for selector in card_selectors:
            found = soup.select(selector)
            if found:
                cards = found
                print(f"    Found {len(cards)} cards using {selector}")
                break
        
        for card in cards:
            parish = self._extract_parish_from_card(card)
            if parish:
                parishes.append(parish)
        
        return self.remove_duplicates(parishes)
    
    def _extract_parish_from_card(self, card) -> Optional[Parish]:
        """Extract parish data from a single card element"""
        # Look for parish name in card title
        title_elem = self._find_title_element(card)
        if not title_elem:
            return None
            
        name = self.clean_text(title_elem.get_text())
        if not self.validate_parish_name(name):
            return None
        
        # Look for city in card body
        city = self._extract_city_from_card(card)
        
        # Look for address and phone in card text
        card_text = card.get_text()
        phone = self.extract_phone(card_text)
        
        # Look for website link
        website = self._extract_website_from_card(card)
        
        return Parish(
            name=name,
            city=city,
            phone=phone,
            website=website,
            confidence=0.8,
            extraction_method="card_layout"
        )
    
    def _find_title_element(self, card):
        """Find the title element in a card"""
        # Try card-specific title classes first
        title_elem = card.find(['h3', 'h4', 'h5'], class_=re.compile(r'.*title.*'))
        if title_elem:
            return title_elem
        
        # Fallback to any heading tag
        return card.find(['h1', 'h2', 'h3', 'h4', 'h5'])
    
    def _extract_city_from_card(self, card) -> Optional[str]:
        """Extract city information from card"""
        # Look in card body
        body = card.find('div', class_='card-body')
        if body:
            text_lines = [line.strip() for line in body.get_text().split('\n') if line.strip()]
            # City is often the second line after parish name
            if len(text_lines) > 1:
                potential_city = text_lines[1]
                if not potential_city.startswith('Learn More') and len(potential_city) < 50:
                    return self.clean_text(potential_city)
        
        return None
    
    def _extract_website_from_card(self, card) -> Optional[str]:
        """Extract website URL from card"""
        links = card.find_all('a', href=True)
        for link in links:
            href = link.get('href')
            if href.startswith('http') and not any(skip in href.lower() 
                                                 for skip in ['facebook', 'twitter', 'instagram']):
                return href
        return None
