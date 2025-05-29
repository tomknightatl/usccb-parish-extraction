# File: tests/test_utils.py

"""Tests for utility functions"""

import pytest
from bs4 import BeautifulSoup
from src.utils.webdriver import clean_text, extract_phone, extract_coordinates
from src.utils.ai_analysis import detect_site_type, validate_parish_name
from src.models import SiteType

class TestWebDriverUtils:
    """Test webdriver utility functions"""
    
    def test_clean_text(self):
        """Test text cleaning function"""
        # Normal text
        assert clean_text("  Hello World  ") == "Hello World"
        
        # Multiple spaces
        assert clean_text("Hello    World") == "Hello World"
        
        # Newlines and tabs
        assert clean_text("Hello\n\tWorld") == "Hello World"
        
        # Empty/None
        assert clean_text("") == ""
        assert clean_text(None) == ""
    
    def test_extract_phone(self):
        """Test phone number extraction"""
        # Standard formats
        assert extract_phone("(216) 555-1234") == "(216) 555-1234"
        assert extract_phone("216-555-1234") == "(216) 555-1234"
        assert extract_phone("216.555.1234") == "(216) 555-1234"
        assert extract_phone("2165551234") == "(216) 555-1234"
        
        # With surrounding text
        assert extract_phone("Call us at (216) 555-1234 today") == "(216) 555-1234"
        
        # No phone number
        assert extract_phone("No phone here") is None
        assert extract_phone("") is None
        assert extract_phone(None) is None
    
    def test_extract_coordinates(self):
        """Test coordinate extraction from HTML elements"""
        # Create mock element with coordinates
        html = '<div data-latitude="41.123" data-longitude="-81.456"></div>'
        soup = BeautifulSoup(html, 'html.parser')
        element = soup.find('div')
        
        lat, lng = extract_coordinates(element)
        assert lat == 41.123
        assert lng == -81.456
        
        # Test with zero coordinates (should return None)
        html = '<div data-latitude="0.0" data-longitude="0.0"></div>'
        soup = BeautifulSoup(html, 'html.parser')
        element = soup.find('div')
        
        lat, lng = extract_coordinates(element)
        assert lat is None
        assert lng is None
        
        # Test with missing coordinates
        html = '<div></div>'
        soup = BeautifulSoup(html, 'html.parser')
        element = soup.find('div')
        
        lat, lng = extract_coordinates(element)
        assert lat is None
        assert lng is None

class TestAIAnalysis:
    """Test AI analysis functions"""
    
    def test_detect_site_type_parish_finder(self):
        """Test parish finder detection"""
        # Test URL-based detection
        soup = BeautifulSoup("<html></html>", 'html.parser')
        assert detect_site_type(soup, "https://diocese.org/parishfinder") == SiteType.PARISH_FINDER
        
        # Test HTML content detection
        html = '<div>Some content</div><li class="site">Parish</li>'
        soup = BeautifulSoup(html, 'html.parser')
        assert detect_site_type(soup, "https://diocese.org") == SiteType.PARISH_FINDER
    
    def test_detect_site_type_card_layout(self):
        """Test card layout detection"""
        html = '<div class="col-lg location">Parish card</div>'
        soup = BeautifulSoup(html, 'html.parser')
        assert detect_site_type(soup, "https://diocese.org") == SiteType.CARD_LAYOUT
    
    def test_detect_site_type_table(self):
        """Test table detection"""
        html = '<table><tr><td>Parish Name</td></tr></table>'
        soup = BeautifulSoup(html, 'html.parser')
        assert detect_site_type(soup, "https://diocese.org") == SiteType.TABLE
    
    def test_detect_site_type_map(self):
        """Test map detection"""
        html = '<div>Content with google.maps integration</div>'
        soup = BeautifulSoup(html, 'html.parser')
        assert detect_site_type(soup, "https://diocese.org") == SiteType.MAP
    
    def test_detect_site_type_generic(self):
        """Test generic fallback"""
        html = '<div>Just some regular content</div>'
        soup = BeautifulSoup(html, 'html.parser')
        assert detect_site_type(soup, "https://diocese.org") == SiteType.GENERIC
    
    def test_validate_parish_name(self):
        """Test parish name validation"""
        # Valid names
        assert validate_parish_name("St. Mary Parish")
        assert validate_parish_name("Holy Trinity Church")
        assert validate_parish_name("Our Lady of Guadalupe")
        assert validate_parish_name("Sacred Heart Cathedral")
        
        # Invalid names
        assert not validate_parish_name("Contact")
        assert not validate_parish_name("Directory")
        assert not validate_parish_name("Search")
        assert not validate_parish_name("Map")
        assert not validate_parish_name("")
        assert not validate_parish_name("Hi")  # Too short
        
        # Edge cases
        assert not validate_parish_name(None)
        assert not validate_parish_name("   ")  # Only whitespace

class TestMockFunctions:
    """Test mock functions when APIs are not available"""
    
    def test_mock_ai_analysis(self):
        """Test that mock AI analysis returns reasonable defaults"""
        from src.utils.ai_analysis import analyze_with_ai
        
        # Should return mock response when no API key
        result = analyze_with_ai("parish directory test", "parish_directory")
        assert 'score' in result
        assert isinstance(result['score'], int)
        assert 0 <= result['score'] <= 10
