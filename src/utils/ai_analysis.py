# File: src/utils/ai_analysis.py

"""AI-powered content analysis using Google Gemini"""

import re
from typing import Dict, Any
import google.generativeai as genai
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import get_config
from ..models import SiteType

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def analyze_with_ai(text: str, query_type: str = "parish_directory") -> Dict[str, Any]:
    """Analyze content with Gemini AI"""
    config = get_config()
    
    if not config.genai_enabled:
        # Return mock response for testing
        mock_responses = {
            "parish_directory": {"score": 7, "reasoning": "Mock response - likely parish directory"},
            "parish_info": '{"name": "Sample Parish", "city": "Sample City"}'
        }
        return mock_responses.get(query_type, {"score": 0})
    
    prompts = {
        "parish_directory": f"""
        Rate 0-10 how likely this link leads to a parish directory, church finder, or list of parishes.
        Look for keywords like: parish, church, directory, finder, locations, worship sites, mass times.
        
        Link information: {text[:500]}
        
        Respond with ONLY a number from 0-10.
        """,
        
        "parish_info": f"""
        Extract parish information from this text. Look for parish name, city, address, phone number, website.
        
        Text: {text[:1000]}
        
        Return as valid JSON with fields: name, city, address, phone, website
        """
    }
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompts[query_type])
        
        if query_type == "parish_directory":
            # Extract score from response
            score_match = re.search(r'(\d+)', response.text)
            score = int(score_match.group(1)) if score_match else 0
            return {"score": min(max(score, 0), 10)}  # Clamp between 0-10
        
        return response.text
        
    except Exception as e:
        print(f"AI analysis failed: {e}")
        return {"score": 0} if query_type == "parish_directory" else "{}"

def detect_site_type(soup: BeautifulSoup, url: str) -> SiteType:
    """Detect website type for optimal extraction strategy"""
    html = str(soup).lower()
    url_lower = url.lower()
    
    # Check for parish finder interfaces (eCatholic and similar)
    finder_indicators = [
        'parishfinder' in url_lower,
        'parish-finder' in url_lower, 
        'find-parish' in url_lower,
        'finder.js' in html,
        'parish finder' in html,
        'findercore' in html,
        soup.find('li', class_='site') is not None
    ]
    
    if any(finder_indicators):
        return SiteType.PARISH_FINDER
    
    # Check for card-based layouts
    card_indicators = [
        soup.find_all('div', class_=re.compile(r'(card.*location|location.*card|parish.*card)')),
        soup.find_all('div', class_='col-lg location'),  # Salt Lake City style
        soup.select('[class*="parish-card"]'),
        soup.select('[class*="location-card"]')
    ]
    
    if any(indicators for indicators in card_indicators):
        return SiteType.CARD_LAYOUT
    
    # Check for HTML tables with parish data
    tables = soup.find_all('table')
    for table in tables:
        if any(keyword in table.get_text().lower() for keyword in ['parish', 'church', 'name', 'address']):
            return SiteType.TABLE
    
    # Check for interactive maps
    map_indicators = [
        'leaflet' in html,
        'google.maps' in html,
        'mapbox' in html,
        'parish-map' in html,
        soup.find(id='map') is not None,
        soup.find(class_='map') is not None
    ]
    
    if any(map_indicators):
        return SiteType.MAP
    
    # Default to generic extraction
    return SiteType.GENERIC

def validate_parish_name(name: str) -> bool:
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
