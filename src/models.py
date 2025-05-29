# File: src/models.py

"""Data models for the parish extraction system"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime

class SiteType(Enum):
    """Types of website layouts we can extract from"""
    PARISH_FINDER = "parish_finder"
    CARD_LAYOUT = "card_layout"
    TABLE = "table"
    MAP = "map"
    GENERIC = "generic"

@dataclass
class Parish:
    """Parish data model"""
    name: str
    city: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    confidence: float = 0.5
    extraction_method: str = "unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            k: v for k, v in {
                'Name': self.name,
                'City': self.city,
                'Street Address': self.address,
                'Phone Number': self.phone,
                'Web': self.website,
                'latitude': self.latitude,
                'longitude': self.longitude,
                'confidence_score': self.confidence,
                'extraction_method': self.extraction_method,
                'extracted_at': datetime.now().isoformat()
            }.items() if v is not None and v != ""
        }
    
    def __str__(self) -> str:
        return f"Parish({self.name}, {self.city or 'Unknown City'})"

@dataclass
class ExtractionResult:
    """Results from parish extraction process"""
    diocese_name: str
    diocese_url: str = ""
    directory_url: str = ""
    parishes: List[Parish] = field(default_factory=list)
    site_type: SiteType = SiteType.GENERIC
    success: bool = True
    errors: List[str] = field(default_factory=list)
    saved_count: int = 0
    processing_time: float = 0.0
    
    @property
    def parish_count(self) -> int:
        """Number of parishes extracted"""
        return len(self.parishes)
    
    @property
    def success_rate(self) -> float:
        """Success rate for saving parishes"""
        if self.parish_count == 0:
            return 0.0
        return self.saved_count / self.parish_count
    
    def add_error(self, error: str):
        """Add an error message"""
        self.errors.append(error)
        self.success = False

@dataclass
class Diocese:
    """Diocese information"""
    name: str
    url: str
    directory_url: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Diocese':
        """Create Diocese from database row"""
        return cls(
            name=data.get('Name', ''),
            url=data.get('Website', ''),
            directory_url=data.get('parish_directory_url')
        )
    
    def __str__(self) -> str:
        return f"Diocese({self.name})"
