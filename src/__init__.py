# File: src/__init__.py

"""USCCB Parish Extraction System

A comprehensive system for extracting Catholic diocese and parish data
from official websites using AI-powered content analysis.
"""

__version__ = "1.0.0"
__author__ = "USCCB Data Project"

from .models import Parish, Diocese, ExtractionResult, SiteType
from .pipeline import ParishExtractionPipeline

__all__ = [
    'Parish',
    'Diocese', 
    'ExtractionResult',
    'SiteType',
    'ParishExtractionPipeline'
]
