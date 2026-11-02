"""
Data validation utilities for the Real Estate Scraper
"""
import re
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

class PropertyValidator:
    """Validator class for property data"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Regex patterns for validation
        self.patterns = {
            'zip_code': re.compile(r'^\d{5}(-\d{4})?$'),
            'phone': re.compile(r'^(\+1-?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}$'),
            'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
            'url': re.compile(r'^https?://[^\s/$.?#].[^\s]*$'),
            'mls_number': re.compile(r'^[A-Z0-9\-]{6,15}$', re.IGNORECASE)
        }
    
    def validate_property(self, property_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a property data dictionary
        Returns: (is_valid, list_of_errors)
        """
        errors = []
        
        # Required fields validation
        required_fields = ['title', 'price', 'address']
        for field in required_fields:
            if not property_data.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Title validation
        title = property_data.get('title', '')
        if title:
            if len(title.strip()) < 5:
                errors.append("Title too short (minimum 5 characters)")
            if len(title) > 200:
                errors.append("Title too long (maximum 200 characters)")
        
        # Price validation
        price = property_data.get('price')
        if price is not None:
            try:
                price_float = float(price)
                if price_float < 0:
                    errors.append("Price cannot be negative")
                elif price_float == 0:
                    errors.append("Price cannot be zero")
                elif price_float > 100000000:  # $100M limit
                    errors.append("Price seems unreasonably high")
                elif price_float < 1000:  # $1K minimum
                    errors.append("Price seems unreasonably low")
            except (ValueError, TypeError):
                errors.append("Invalid price format")
        
        # Address validation
        address = property_data.get('address', '')
        if address:
            if len(address.strip()) < 10:
                errors.append("Address too short")
            if not re.search(r'\d', address):
                errors.append("Address should contain a street number")
        
        # Bedrooms validation
        bedrooms = property_data.get('bedrooms')
        if bedrooms is not None:
            try:
                bed_int = int(bedrooms)
                if bed_int < 0:
                    errors.append("Bedrooms cannot be negative")
                elif bed_int > 20:
                    errors.append("Bedrooms count seems unreasonable")
            except (ValueError, TypeError):
                errors.append("Invalid bedrooms format")
        
        # Bathrooms validation
        bathrooms = property_data.get('bathrooms')
        if bathrooms is not None:
            try:
                bath_float = float(bathrooms)
                if bath_float < 0:
                    errors.append("Bathrooms cannot be negative")
                elif bath_float > 20:
                    errors.append("Bathrooms count seems unreasonable")
            except (ValueError, TypeError):
                errors.append("Invalid bathrooms format")
        
        # Square feet validation
        square_feet = property_data.get('square_feet')
        if square_feet is not None:
            try:
                sqft_float = float(square_feet)
                if sqft_float < 0:
                    errors.append("Square feet cannot be negative")
                elif sqft_float < 100:
                    errors.append("Square feet seems too small")
                elif sqft_float > 50000:
                    errors.append("Square feet seems unreasonably large")
            except (ValueError, TypeError):
                errors.append("Invalid square feet format")
        
        # Year built validation
        year_built = property_data.get('year_built')
        if year_built is not None:
            try:
                year_int = int(year_built)
                current_year = datetime.now().year
                if year_int < 1800:
                    errors.append("Year built seems too old")
                elif year_int > current_year + 5:
                    errors.append("Year built is in the future")
            except (ValueError, TypeError):
                errors.append("Invalid year built format")
        
        # ZIP code validation
        zip_code = property_data.get('zip_code', '')
        if zip_code and not self.patterns['zip_code'].match(str(zip_code)):
            errors.append("Invalid ZIP code format")
        
        # MLS number validation
        mls_number = property_data.get('mls_number', '')
        if mls_number and not self.patterns['mls_number'].match(str(mls_number)):
            errors.append("Invalid MLS number format")
        
        # URL validation
        source_url = property_data.get('source_url', '')
        if source_url and not self.patterns['url'].match(str(source_url)):
            errors.append("Invalid source URL format")
        
        virtual_tour_url = property_data.get('virtual_tour_url', '')
        if virtual_tour_url and not self.patterns['url'].match(str(virtual_tour_url)):
            errors.append("Invalid virtual tour URL format")
        
        # Property type validation
        property_type = property_data.get('property_type', '')
        valid_types = ['house', 'condo', 'townhouse', 'apartment', 'duplex', 'land', 'commercial', 'other']
        if property_type and property_type.lower() not in valid_types:
            errors.append(f"Invalid property type. Must be one of: {', '.join(valid_types)}")
        
        return len(errors) == 0, errors
    
    def clean_property_data(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize property data"""
        cleaned = property_data.copy()
        
        # Clean text fields
        text_fields = ['title', 'address', 'city', 'state', 'description', 'listing_agent', 'listing_agency']
        for field in text_fields:
            if cleaned.get(field):
                cleaned[field] = self.clean_text(str(cleaned[field]))
        
        # Normalize property type
        if cleaned.get('property_type'):
            cleaned['property_type'] = self.normalize_property_type(str(cleaned['property_type']))
        
        # Clean price
        if cleaned.get('price'):
            cleaned['price'] = self.clean_price(cleaned['price'])
        
        # Clean numeric fields
        numeric_fields = ['bedrooms', 'bathrooms', 'square_feet', 'lot_size', 'year_built', 'days_on_market']
        for field in numeric_fields:
            if cleaned.get(field):
                cleaned[field] = self.clean_numeric(cleaned[field])
        
        # Clean lists
        list_fields = ['features', 'amenities', 'images']
        for field in list_fields:
            if cleaned.get(field):
                cleaned[field] = self.clean_list(cleaned[field])
        
        return cleaned
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', str(text).strip())
        
        # Remove special characters that might cause issues
        text = re.sub(r'[^\w\s\-.,()&$/]', '', text)
        
        # Capitalize properly
        if len(text) > 0:
            text = text[0].upper() + text[1:]
        
        return text
    
    def clean_price(self, price) -> Optional[float]:
        """Extract and clean price from various formats"""
        if price is None:
            return None
        
        # Convert to string and remove currency symbols and commas
        price_str = str(price).replace('$', '').replace(',', '').strip()
        
        # Handle "K" and "M" suffixes
        if price_str.lower().endswith('k'):
            price_str = price_str[:-1]
            multiplier = 1000
        elif price_str.lower().endswith('m'):
            price_str = price_str[:-1]
            multiplier = 1000000
        else:
            multiplier = 1
        
        try:
            return float(price_str) * multiplier
        except (ValueError, TypeError):
            return None
    
    def clean_numeric(self, value) -> Optional[float]:
        """Clean numeric values"""
        if value is None:
            return None
        
        try:
            # Remove commas and convert to float
            if isinstance(value, str):
                value = value.replace(',', '')
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def clean_list(self, value) -> List[str]:
        """Clean list values"""
        if not value:
            return []
        
        if isinstance(value, str):
            # Split by common delimiters
            items = re.split(r'[,;|]', value)
        elif isinstance(value, list):
            items = value
        else:
            items = [str(value)]
        
        # Clean each item
        cleaned_items = []
        for item in items:
            cleaned_item = self.clean_text(str(item))
            if cleaned_item and cleaned_item not in cleaned_items:
                cleaned_items.append(cleaned_item)
        
        return cleaned_items
    
    def normalize_property_type(self, property_type: str) -> str:
        """Normalize property type to standard values"""
        property_type = property_type.lower().strip()
        
        # Mapping for common variations
        mappings = {
            'single family': 'house',
            'single-family': 'house',
            'single family home': 'house',
            'sfh': 'house',
            'detached': 'house',
            'condominium': 'condo',
            'co-op': 'condo',
            'cooperative': 'condo',
            'townhome': 'townhouse',
            'town house': 'townhouse',
            'town home': 'townhouse',
            'apt': 'apartment',
            'flat': 'apartment',
            'multi-family': 'duplex',
            'multifamily': 'duplex',
            'vacant land': 'land',
            'lot': 'land'
        }
        
        return mappings.get(property_type, property_type)

class AddressParser:
    """Parse and validate addresses"""
    
    def __init__(self):
        self.state_abbreviations = {
            'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR', 'california': 'CA',
            'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE', 'florida': 'FL', 'georgia': 'GA',
            'hawaii': 'HI', 'idaho': 'ID', 'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA',
            'kansas': 'KS', 'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
            'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS', 'missouri': 'MO',
            'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV', 'new hampshire': 'NH', 'new jersey': 'NJ',
            'new mexico': 'NM', 'new york': 'NY', 'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH',
            'oklahoma': 'OK', 'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
            'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT', 'vermont': 'VT',
            'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV', 'wisconsin': 'WI', 'wyoming': 'WY'
        }
    
    def parse_address(self, address: str) -> Dict[str, Optional[str]]:
        """Parse address into components"""
        if not address:
            return {'street': None, 'city': None, 'state': None, 'zip_code': None}
        
        # Basic regex patterns for address components
        zip_match = re.search(r'\b(\d{5}(?:-\d{4})?)\b', address)
        zip_code = zip_match.group(1) if zip_match else None
        
        # Remove ZIP code from address for further parsing
        address_without_zip = re.sub(r'\b\d{5}(?:-\d{4})?\b', '', address).strip()
        
        # Split by commas
        parts = [part.strip() for part in address_without_zip.split(',')]
        
        if len(parts) >= 3:
            street = parts[0]
            city = parts[1]
            state = self.normalize_state(parts[2])
        elif len(parts) == 2:
            street = parts[0]
            city_state = parts[1].strip()
            # Try to extract state from the end
            state_match = re.search(r'\b([A-Z]{2})\s*$', city_state)
            if state_match:
                state = state_match.group(1)
                city = city_state[:state_match.start()].strip()
            else:
                city = city_state
                state = None
        else:
            street = address_without_zip
            city = None
            state = None
        
        return {
            'street': street if street else None,
            'city': city if city else None,
            'state': state if state else None,
            'zip_code': zip_code
        }
    
    def normalize_state(self, state: str) -> Optional[str]:
        """Normalize state to 2-letter abbreviation"""
        if not state:
            return None
        
        state = state.strip().lower()
        
        # If already 2 letters, convert to uppercase
        if len(state) == 2 and state.isalpha():
            return state.upper()
        
        # Look up full state name
        return self.state_abbreviations.get(state)