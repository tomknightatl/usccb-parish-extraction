# File: src/extractors/__init__.py

"""Parish extraction modules for different website types"""

from .base import BaseExtractor
from .parish_finder import ParishFinderExtractor
from .card_layout import CardLayoutExtractor
from .table import TableExtractor
from .generic import GenericExtractor

# Extractor registry for easy access
EXTRACTORS = {
    'parish_finder': ParishFinderExtractor,
    'card_layout': CardLayoutExtractor, 
    'table': TableExtractor,
    'generic': GenericExtractor
}

def get_extractor(site_type: str) -> BaseExtractor:
    """Get the appropriate extractor for a site type"""
    extractor_class = EXTRACTORS.get(site_type, GenericExtractor)
    return extractor_class()

__all__ = [
    'BaseExtractor',
    'ParishFinderExtractor',
    'CardLayoutExtractor', 
    'TableExtractor',
    'GenericExtractor',
    'get_extractor',
    'EXTRACTORS'
]
