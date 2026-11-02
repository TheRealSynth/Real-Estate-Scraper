"""
Data models for real estate properties
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class Property:
    """Main property data model"""
    id: Optional[str] = None
    title: Optional[str] = None
    price: Optional[float] = None
    price_currency: str = "USD"
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: str = "USA"
    
    # Property details
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[float] = None
    lot_size: Optional[float] = None
    year_built: Optional[int] = None
    property_type: Optional[str] = None  # house, condo, townhouse, etc.
    
    # Listing details
    listing_agent: Optional[str] = None
    listing_agency: Optional[str] = None
    listing_date: Optional[datetime] = None
    days_on_market: Optional[int] = None
    mls_number: Optional[str] = None
    
    # Features and amenities
    features: List[str] = field(default_factory=list)
    amenities: List[str] = field(default_factory=list)
    
    # Additional info
    description: Optional[str] = None
    images: List[str] = field(default_factory=list)
    virtual_tour_url: Optional[str] = None
    
    # Metadata
    source_url: Optional[str] = None
    source_website: Optional[str] = None
    scraped_at: datetime = field(default_factory=datetime.now)
    
    # Raw data for debugging
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert property to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'price': self.price,
            'price_currency': self.price_currency,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'country': self.country,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'square_feet': self.square_feet,
            'lot_size': self.lot_size,
            'year_built': self.year_built,
            'property_type': self.property_type,
            'listing_agent': self.listing_agent,
            'listing_agency': self.listing_agency,
            'listing_date': self.listing_date.isoformat() if self.listing_date else None,
            'days_on_market': self.days_on_market,
            'mls_number': self.mls_number,
            'features': self.features,
            'amenities': self.amenities,
            'description': self.description,
            'images': self.images,
            'virtual_tour_url': self.virtual_tour_url,
            'source_url': self.source_url,
            'source_website': self.source_website,
            'scraped_at': self.scraped_at.isoformat()
        }

@dataclass
class SearchCriteria:
    """Search criteria for property scraping"""
    location: str
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_bedrooms: Optional[int] = None
    max_bedrooms: Optional[int] = None
    min_bathrooms: Optional[float] = None
    max_bathrooms: Optional[float] = None
    property_types: List[str] = field(default_factory=list)
    max_pages: Optional[int] = None