# File: tests/test_extractors.py

"""Tests for parish extractors"""

import pytest
from bs4 import BeautifulSoup
from src.extractors import get_extractor, ParishFinderExtractor, CardLayoutExtractor, TableExtractor, GenericExtractor
from src.models import Parish

class TestExtractors:
    """Test cases for parish extractors"""
    
    def test_get_extractor(self):
        """Test extractor factory function"""
        # Test known extractors
        assert isinstance(get_extractor('parish_finder'), ParishFinderExtractor)
        assert isinstance(get_extractor('card_layout'), CardLayoutExtractor)
        assert isinstance(get_extractor('table'), TableExtractor)
        
        # Test unknown extractor defaults to generic
        assert isinstance(get_extractor('unknown'), GenericExtractor)
    
    def test_parish_finder_extractor(self):
        """Test parish finder extractor with sample HTML"""
        html = '''
        <ul>
            <li class="site" data-latitude="41.123" data-longitude="-81.456">
                <div class="name">St. Mary Parish</div>
                <div class="city">Cleveland</div>
                <div class="siteInfo">
                    <div class="main">
                        <div class="title">
                            <div class="address">123 Main St, Cleveland, OH 44111</div>
                            <div class="phoneFaxHolder">
                                <span class="phone">(216) 555-1234</span>
                            </div>
                        </div>
                        <div class="linkContainer">
                            <a class="urlLink" href="https://stmary.org">Website</a>
                        </div>
                    </div>
                </div>
            </li>
        </ul>
        '''
        
        soup = BeautifulSoup(html, 'html.parser')
        extractor = ParishFinderExtractor()
        parishes = extractor.extract(soup, "https://test.org")
        
        assert len(parishes) == 1
        parish = parishes[0]
        assert parish.name == "St. Mary Parish"
        assert parish.city == "Cleveland"
        assert parish.address == "123 Main St, Cleveland, OH 44111"
        assert parish.phone == "(216) 555-1234"
        assert parish.website == "https://stmary.org"
        assert parish.latitude == 41.123
        assert parish.longitude == -81.456
    
    def test_card_layout_extractor(self):
        """Test card layout extractor"""
        html = '''
        <div class="col-lg location">
            <a class="card">
                <h4 class="card-title">Holy Trinity Parish</h4>
                <div class="card-body">
                    <div>Salt Lake City</div>
                    <div>Learn More</div>
                </div>
            </a>
        </div>
        '''
        
        soup = BeautifulSoup(html, 'html.parser')
        extractor = CardLayoutExtractor()
        parishes = extractor.extract(soup, "https://test.org")
        
        assert len(parishes) == 1
        parish = parishes[0]
        assert parish.name == "Holy Trinity Parish"
        assert parish.city == "Salt Lake City"
    
    def test_table_extractor(self):
        """Test table extractor"""
        html = '''
        <table>
            <tr><th>Parish Name</th><th>City</th><th>Phone</th></tr>
            <tr>
                <td>St. Joseph Church</td>
                <td>Denver</td>
                <td>(303) 555-9876</td>
            </tr>
        </table>
        '''
        
        soup = BeautifulSoup(html, 'html.parser')
        extractor = TableExtractor()
        parishes = extractor.extract(soup, "https://test.org")
        
        assert len(parishes) == 1
        parish = parishes[0]
        assert parish.name == "St. Joseph Church"
        assert parish.city == "Denver"
        assert parish.phone == "(303) 555-9876"
    
    def test_generic_extractor(self):
        """Test generic extractor"""
        html = '''
        <article class="parish-item">
            <h3>Our Lady of Grace Parish</h3>
            <p>Located in beautiful downtown area</p>
            <p>Phone: (555) 123-4567</p>
            <a href="https://ourladyofgrace.org">Visit Website</a>
        </article>
        '''
        
        soup = BeautifulSoup(html, 'html.parser')
        extractor = GenericExtractor()
        parishes = extractor.extract(soup, "https://test.org")
        
        assert len(parishes) == 1
        parish = parishes[0]
        assert parish.name == "Our Lady of Grace Parish"
        assert parish.phone == "(555) 123-4567"
        assert parish.website == "https://ourladyofgrace.org"
    
    def test_validate_parish_name(self):
        """Test parish name validation"""
        extractor = GenericExtractor()
        
        # Valid parish names
        assert extractor.validate_parish_name("St. Mary Parish")
        assert extractor.validate_parish_name("Holy Trinity Church")
        assert extractor.validate_parish_name("Our Lady of Grace")
        assert extractor.validate_parish_name("Sacred Heart Cathedral")
        
        # Invalid parish names
        assert not extractor.validate_parish_name("Contact Us")
        assert not extractor.validate_parish_name("Directory")
        assert not extractor.validate_parish_name("Search")
        assert not extractor.validate_parish_name("")
        assert not extractor.validate_parish_name("ab")  # Too short
    
    def test_remove_duplicates(self):
        """Test duplicate removal"""
        extractor = GenericExtractor()
        
        parishes = [
            Parish(name="St. Mary Parish", city="Cleveland"),
            Parish(name="St. Mary Parish", city="Cleveland"),  # Duplicate
            Parish(name="Holy Trinity", city="Denver"),
            Parish(name="Contact Office", city="Denver"),  # Invalid name
        ]
        
        unique_parishes = extractor.remove_duplicates(parishes)
        
        assert len(unique_parishes) == 2
        names = [p.name for p in unique_parishes]
        assert "St. Mary Parish" in names
        assert "Holy Trinity" in names
        assert "Contact Office" not in names
