"""Data processing utilities for real estate data."""

import re
import json
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from ..scrapers.base_scraper import Property
from .logger import setup_logger


class DataProcessor:
    """Process and clean scraped real estate data."""
    
    def __init__(self, config):
        self.config = config
        self.logger = setup_logger("DataProcessor", level=config.log_level)
    
    def process_properties(self, properties: List[Property]) -> List[Property]:
        """Clean and standardize a list of properties."""
        processed = []
        
        for prop in properties:
            try:
                cleaned_prop = self._clean_property(prop)
                if self._is_valid_property(cleaned_prop):
                    processed.append(cleaned_prop)
                else:
                    self.logger.debug(f"Filtered out invalid property: {prop.address}")
            except Exception as e:
                self.logger.warning(f"Error processing property {prop.address}: {str(e)}")
        
        self.logger.info(f"Processed {len(processed)} valid properties from {len(properties)} total")
        return processed
    
    def _clean_property(self, prop: Property) -> Property:
        """Clean and standardize a single property."""
        # Clean address components
        prop.address = self._clean_address(prop.address)
        prop.city = self._clean_city(prop.city)
        prop.state = self._clean_state(prop.state)
        prop.zip_code = self._clean_zip_code(prop.zip_code)
        
        # Clean numeric fields
        prop.price = self._clean_price_value(prop.price)
        prop.bedrooms = self._clean_bedrooms(prop.bedrooms)
        prop.bathrooms = self._clean_bathrooms(prop.bathrooms)
        prop.square_feet = self._clean_square_feet(prop.square_feet)
        prop.lot_size = self._clean_lot_size(prop.lot_size)
        prop.year_built = self._clean_year_built(prop.year_built)
        
        # Clean text fields
        prop.property_type = self._clean_property_type(prop.property_type)
        prop.description = self._clean_description(prop.description)
        prop.listing_agent = self._clean_agent_name(prop.listing_agent)
        
        # Clean arrays
        prop.features = self._clean_features(prop.features)
        prop.photos = self._clean_photo_urls(prop.photos)
        
        return prop
    
    def _clean_address(self, address: str) -> str:
        """Clean and standardize address."""
        if not address:
            return ""
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', address.strip())
        
        # Standardize common abbreviations
        replacements = {
            r'\bSt\b': 'Street',
            r'\bAve\b': 'Avenue',
            r'\bBlvd\b': 'Boulevard',
            r'\bDr\b': 'Drive',
            r'\bRd\b': 'Road',
            r'\bLn\b': 'Lane',
            r'\bCt\b': 'Court',
            r'\bPl\b': 'Place',
            r'\bPkwy\b': 'Parkway',
            r'\bHwy\b': 'Highway',
        }
        
        for pattern, replacement in replacements.items():
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        
        return cleaned.title()
    
    def _clean_city(self, city: str) -> str:
        """Clean and standardize city name."""
        if not city:
            return ""
        
        # Remove extra whitespace and title case
        cleaned = re.sub(r'\s+', ' ', city.strip()).title()
        
        # Remove any trailing state abbreviations that might be included
        cleaned = re.sub(r',?\s+[A-Z]{2}$', '', cleaned)
        
        return cleaned
    
    def _clean_state(self, state: str) -> str:
        """Clean and standardize state."""
        if not state:
            return ""
        
        state = state.strip().upper()
        
        # State abbreviation mapping
        state_mapping = {
            'ALABAMA': 'AL', 'ALASKA': 'AK', 'ARIZONA': 'AZ', 'ARKANSAS': 'AR',
            'CALIFORNIA': 'CA', 'COLORADO': 'CO', 'CONNECTICUT': 'CT', 'DELAWARE': 'DE',
            'FLORIDA': 'FL', 'GEORGIA': 'GA', 'HAWAII': 'HI', 'IDAHO': 'ID',
            'ILLINOIS': 'IL', 'INDIANA': 'IN', 'IOWA': 'IA', 'KANSAS': 'KS',
            'KENTUCKY': 'KY', 'LOUISIANA': 'LA', 'MAINE': 'ME', 'MARYLAND': 'MD',
            'MASSACHUSETTS': 'MA', 'MICHIGAN': 'MI', 'MINNESOTA': 'MN', 'MISSISSIPPI': 'MS',
            'MISSOURI': 'MO', 'MONTANA': 'MT', 'NEBRASKA': 'NE', 'NEVADA': 'NV',
            'NEW HAMPSHIRE': 'NH', 'NEW JERSEY': 'NJ', 'NEW MEXICO': 'NM', 'NEW YORK': 'NY',
            'NORTH CAROLINA': 'NC', 'NORTH DAKOTA': 'ND', 'OHIO': 'OH', 'OKLAHOMA': 'OK',
            'OREGON': 'OR', 'PENNSYLVANIA': 'PA', 'RHODE ISLAND': 'RI', 'SOUTH CAROLINA': 'SC',
            'SOUTH DAKOTA': 'SD', 'TENNESSEE': 'TN', 'TEXAS': 'TX', 'UTAH': 'UT',
            'VERMONT': 'VT', 'VIRGINIA': 'VA', 'WASHINGTON': 'WA', 'WEST VIRGINIA': 'WV',
            'WISCONSIN': 'WI', 'WYOMING': 'WY', 'DISTRICT OF COLUMBIA': 'DC'
        }
        
        return state_mapping.get(state, state)
    
    def _clean_zip_code(self, zip_code: str) -> str:
        """Clean and standardize zip code."""
        if not zip_code:
            return ""
        
        # Extract 5-digit or 5+4 zip code
        match = re.search(r'(\d{5})(?:-(\d{4}))?', str(zip_code))
        if match:
            if match.group(2):
                return f"{match.group(1)}-{match.group(2)}"
            else:
                return match.group(1)
        
        return ""
    
    def _clean_price_value(self, price: Any) -> Optional[float]:
        """Clean and validate price value."""
        if price is None:
            return None
        
        if isinstance(price, str):
            # Remove currency symbols and convert to float
            cleaned = re.sub(r'[^\d.]', '', price)
            try:
                price = float(cleaned)
            except ValueError:
                return None
        
        if isinstance(price, (int, float)):
            # Validate reasonable price range
            if 1000 <= price <= 100000000:  # $1K to $100M
                return float(price)
        
        return None
    
    def _clean_bedrooms(self, bedrooms: Any) -> Optional[int]:
        """Clean and validate bedroom count."""
        if bedrooms is None:
            return None
        
        try:
            beds = int(float(bedrooms))
            if 0 <= beds <= 20:  # Reasonable range
                return beds
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _clean_bathrooms(self, bathrooms: Any) -> Optional[float]:
        """Clean and validate bathroom count."""
        if bathrooms is None:
            return None
        
        try:
            baths = float(bathrooms)
            if 0 <= baths <= 20:  # Reasonable range
                return baths
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _clean_square_feet(self, sqft: Any) -> Optional[int]:
        """Clean and validate square footage."""
        if sqft is None:
            return None
        
        if isinstance(sqft, str):
            # Remove commas and extract number
            cleaned = re.sub(r'[^\d]', '', sqft)
            try:
                sqft = int(cleaned)
            except ValueError:
                return None
        
        try:
            sqft = int(float(sqft))
            if 100 <= sqft <= 50000:  # Reasonable range
                return sqft
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _clean_lot_size(self, lot_size: Any) -> Optional[float]:
        """Clean and validate lot size."""
        if lot_size is None:
            return None
        
        try:
            size = float(lot_size)
            if 0 < size <= 1000:  # Reasonable range in acres
                return size
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _clean_year_built(self, year: Any) -> Optional[int]:
        """Clean and validate year built."""
        if year is None:
            return None
        
        try:
            year = int(float(year))
            current_year = datetime.now().year
            if 1800 <= year <= current_year + 2:  # Reasonable range
                return year
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _clean_property_type(self, prop_type: str) -> Optional[str]:
        """Clean and standardize property type."""
        if not prop_type:
            return None
        
        # Standardize common property types
        prop_type = prop_type.lower().strip()
        
        type_mapping = {
            'single family home': 'Single Family',
            'single-family': 'Single Family',
            'house': 'Single Family',
            'condo': 'Condo',
            'condominium': 'Condo',
            'townhouse': 'Townhouse',
            'townhome': 'Townhouse',
            'apartment': 'Apartment',
            'multi-family': 'Multi-Family',
            'duplex': 'Multi-Family',
            'triplex': 'Multi-Family',
            'mobile home': 'Mobile Home',
            'manufactured home': 'Mobile Home',
            'land': 'Land',
            'lot': 'Land',
            'commercial': 'Commercial',
        }
        
        for key, value in type_mapping.items():
            if key in prop_type:
                return value
        
        return prop_type.title()
    
    def _clean_description(self, description: str) -> Optional[str]:
        """Clean property description."""
        if not description:
            return None
        
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', description.strip())
        
        # Remove HTML tags if any
        cleaned = re.sub(r'<[^>]+>', '', cleaned)
        
        # Limit length
        if len(cleaned) > 5000:
            cleaned = cleaned[:5000] + "..."
        
        return cleaned if cleaned else None
    
    def _clean_agent_name(self, agent: str) -> Optional[str]:
        """Clean listing agent name."""
        if not agent:
            return None
        
        # Remove extra whitespace and title case
        cleaned = re.sub(r'\s+', ' ', agent.strip()).title()
        
        # Remove common titles/suffixes
        cleaned = re.sub(r'\b(Agent|Realtor|Broker|Inc\.?|LLC|Corp\.?|Co\.?)\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.strip()
        
        return cleaned if cleaned else None
    
    def _clean_features(self, features: List[str]) -> List[str]:
        """Clean and standardize property features."""
        if not features:
            return []
        
        cleaned_features = []
        for feature in features:
            if isinstance(feature, str) and feature.strip():
                # Clean and standardize
                cleaned = feature.strip().title()
                if cleaned not in cleaned_features:
                    cleaned_features.append(cleaned)
        
        return cleaned_features
    
    def _clean_photo_urls(self, photos: List[str]) -> List[str]:
        """Clean and validate photo URLs."""
        if not photos:
            return []
        
        cleaned_photos = []
        for photo in photos:
            if isinstance(photo, str) and photo.strip():
                # Basic URL validation
                if photo.startswith(('http://', 'https://')):
                    cleaned_photos.append(photo.strip())
        
        return cleaned_photos
    
    def _is_valid_property(self, prop: Property) -> bool:
        """Check if property has minimum required data."""
        # Must have address and city
        if not prop.address or not prop.city:
            return False
        
        # Must have either price or some basic property info
        if not prop.price and not any([prop.bedrooms, prop.bathrooms, prop.square_feet]):
            return False
        
        return True
    
    def deduplicate_properties(self, properties: List[Property]) -> List[Property]:
        """Remove duplicate properties based on address and price."""
        seen = set()
        deduplicated = []
        
        for prop in properties:
            # Create a key for deduplication
            key = (
                prop.address.lower() if prop.address else "",
                prop.city.lower() if prop.city else "",
                prop.state if prop.state else "",
                prop.price if prop.price else 0
            )
            
            if key not in seen:
                seen.add(key)
                deduplicated.append(prop)
            else:
                self.logger.debug(f"Removed duplicate property: {prop.address}")
        
        self.logger.info(f"Removed {len(properties) - len(deduplicated)} duplicates")
        return deduplicated
    
    def filter_properties(self, properties: List[Property], filters: Dict[str, Any]) -> List[Property]:
        """Filter properties based on criteria."""
        filtered = []
        
        for prop in properties:
            if self._property_matches_filters(prop, filters):
                filtered.append(prop)
        
        self.logger.info(f"Filtered to {len(filtered)} properties from {len(properties)}")
        return filtered
    
    def _property_matches_filters(self, prop: Property, filters: Dict[str, Any]) -> bool:
        """Check if property matches filter criteria."""
        # Price range
        if 'min_price' in filters and prop.price:
            if prop.price < filters['min_price']:
                return False
        
        if 'max_price' in filters and prop.price:
            if prop.price > filters['max_price']:
                return False
        
        # Bedrooms
        if 'min_bedrooms' in filters and prop.bedrooms:
            if prop.bedrooms < filters['min_bedrooms']:
                return False
        
        # Bathrooms
        if 'min_bathrooms' in filters and prop.bathrooms:
            if prop.bathrooms < filters['min_bathrooms']:
                return False
        
        # Square feet
        if 'min_sqft' in filters and prop.square_feet:
            if prop.square_feet < filters['min_sqft']:
                return False
        
        if 'max_sqft' in filters and prop.square_feet:
            if prop.square_feet > filters['max_sqft']:
                return False
        
        # Property type
        if 'property_types' in filters and prop.property_type:
            if prop.property_type not in filters['property_types']:
                return False
        
        # Location
        if 'states' in filters and prop.state:
            if prop.state not in filters['states']:
                return False
        
        if 'cities' in filters and prop.city:
            if prop.city not in filters['cities']:
                return False
        
        return True