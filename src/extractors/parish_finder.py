# File: src/extractors/parish_finder.py

"""Extractor for eCatholic Parish Finder interfaces"""

from typing import List, Optional
from bs4 import BeautifulSoup
from selenium import webdriver

from .base import BaseExtractor
from ..models import Parish
from ..utils.webdriver import extract_coordinates

class ParishFinderExtractor(BaseExtractor):
    """Extract parishes from eCatholic parish finder interfaces"""
    
    def extract(self, soup: BeautifulSoup, url: str, driver: webdriver.Chrome = None) -> List[Parish]:
        """Extract parishes from parish finder page"""
        parishes = []
        
        # Look for parish sites in the finder
        sites = soup.find_all('li', class_='site')
        print(f"    Found {len(sites)} potential parish sites")
        
        for site in sites:
            parish = self._extract_parish_from_site(site)
            if parish:
                parishes.append(parish)
        
        return self.remove_duplicates(parishes)
    
    def _extract_parish_from_site(self, site) -> Optional[Parish]:
        """Extract parish data from a single site element"""
        # Get parish name
        name_elem = site.find('div', class_='name')
        if not name_elem:
            return None
            
        name = self.clean_text(name_elem.get_text())
        if not self.validate_parish_name(name):
            return None
        
        # Get basic location info
        city_elem = site.find('div', class_='city')
        city = self.clean_text(city_elem.get_text()) if city_elem else None
        
        # Get detailed info from siteInfo section
        address = phone = website = None
        site_info = site.find('div', class_='siteInfo')
        
        if site_info:
            address, phone, website = self._extract_from_site_info(site_info)
        
        # Get coordinates from data attributes
        latitude, longitude = extract_coordinates(site)
        
        return Parish(
            name=name,
            city=city,
            address=address,
            phone=phone,
            website=website,
            latitude=latitude,
            longitude=longitude,
            confidence=0.9,
            extraction_method="parish_finder"
        )
    
    def _extract_from_site_info(self, site_info) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Extract detailed information from siteInfo section"""
        address = phone = website = None
        
        # Look for address and phone in title section
        title_section = site_info.find('div', class_='title')
        if title_section:
            address_elem = title_section.find('div', class_='address')
            if address_elem:
                address = self.clean_text(address_elem.get_text())
            
            # Look for phone
            phone_elem = title_section.find('span', class_='phone')
            if phone_elem:
                phone = self.extract_phone(phone_elem.get_text())
        
        # Look for website in link container
        link_container = site_info.find('div', class_='linkContainer')
        if link_container:
            url_link = link_container.find('a', class_='urlLink')
            if url_link:
                website = url_link.get('href')
        
        return address, phone, website
