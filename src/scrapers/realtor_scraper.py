"""Realtor.com real estate scraper."""

import re
import json
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, quote

from .base_scraper import BaseScraper, Property


class RealtorScraper(BaseScraper):
    """Scraper for Realtor.com real estate listings."""
    
    BASE_URL = "https://www.realtor.com"
    SEARCH_URL = "https://www.realtor.com/realestateandhomes-search"
    API_URL = "https://www.realtor.com/api/v1/hulk_web/search"
    
    def __init__(self, config):
        super().__init__(config)
        self.logger.info("Initialized Realtor.com scraper")
    
    def scrape_listings(self, search_params: Dict[str, Any]) -> List[Property]:
        """
        Scrape Realtor.com listings based on search parameters.
        
        Args:
            search_params: Dictionary containing search criteria like:
                - location (str): City, state, or zip code
                - min_price (int): Minimum price
                - max_price (int): Maximum price
                - bedrooms (int): Number of bedrooms
                - bathrooms (int): Number of bathrooms
                - property_type (str): Property type
        """
        properties = []
        
        # Build search URL
        search_url = self._build_search_url(search_params)
        self.logger.info(f"Searching Realtor.com with URL: {search_url}")
        
        try:
            soup = self._get_page(search_url)
            if not soup:
                return properties
            
            # Extract property listings from the page
            listings = self._extract_listings_from_page(soup)
            properties.extend(listings)
            
            # Handle pagination - Realtor.com typically loads more via AJAX
            # For now, we'll just get the first page
            
        except Exception as e:
            self.logger.error(f"Error scraping Realtor.com listings: {str(e)}")
        
        self.logger.info(f"Total properties found: {len(properties)}")
        return properties
    
    def scrape_property_details(self, property_url: str) -> Optional[Property]:
        """Scrape detailed information for a specific Realtor.com property."""
        try:
            soup = self._get_page(property_url)
            if not soup:
                return None
            
            return self._extract_property_details(soup, property_url)
        
        except Exception as e:
            self.logger.error(f"Error scraping property details from {property_url}: {str(e)}")
            return None
    
    def _build_search_url(self, search_params: Dict[str, Any]) -> str:
        """Build Realtor.com search URL from parameters."""
        params = {}
        
        # Location
        if 'location' in search_params:
            location = search_params['location'].replace(' ', '-').replace(',', '')
            base_url = f"{self.SEARCH_URL}/{quote(location)}"
        else:
            base_url = self.SEARCH_URL
        
        # Price range
        if 'min_price' in search_params:
            params['price-min'] = search_params['min_price']
        if 'max_price' in search_params:
            params['price-max'] = search_params['max_price']
        
        # Bedrooms and bathrooms
        if 'bedrooms' in search_params:
            params['beds-min'] = search_params['bedrooms']
        if 'bathrooms' in search_params:
            params['baths-min'] = search_params['bathrooms']
        
        # Property type
        if 'property_type' in search_params:
            type_mapping = {
                'house': 'single-family-home',
                'condo': 'condo',
                'townhouse': 'townhome',
                'apartment': 'condo'
            }
            prop_type = type_mapping.get(search_params['property_type'].lower(), 
                                       search_params['property_type'])
            params['type'] = prop_type
        
        if params:
            return f"{base_url}?{urlencode(params)}"
        else:
            return base_url
    
    def _extract_listings_from_page(self, soup) -> List[Property]:
        """Extract property listings from a Realtor.com search results page."""
        properties = []
        
        # Try to find script tag with property data
        script_tags = soup.find_all('script', type='application/ld+json')
        for script in script_tags:
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    for item in data:
                        if item.get('@type') == 'Product':
                            prop = self._parse_structured_data(item)
                            if prop:
                                properties.append(prop)
            except Exception as e:
                self.logger.warning(f"Could not parse structured data: {str(e)}")
        
        # Fallback to HTML parsing
        if not properties:
            properties = self._extract_from_html(soup)
        
        return properties
    
    def _extract_from_html(self, soup) -> List[Property]:
        """Extract properties from HTML elements (fallback method)."""
        properties = []
        
        # Look for property cards
        cards = soup.find_all('div', {'data-testid': 'property-card'})
        if not cards:
            cards = soup.find_all('div', class_=re.compile(r'BasePropertyCard'))
        if not cards:
            cards = soup.find_all('li', class_=re.compile(r'component_property-card'))
        
        for card in cards:
            try:
                prop = self._parse_card_html(card)
                if prop:
                    properties.append(prop)
            except Exception as e:
                self.logger.warning(f"Error parsing property card: {str(e)}")
        
        return properties
    
    def _parse_structured_data(self, data: dict) -> Optional[Property]:
        """Parse property data from structured JSON-LD data."""
        try:
            # Extract address
            address_info = data.get('address', {})
            if isinstance(address_info, str):
                # Simple address string
                address_parts = address_info.split(', ')
                street_address = address_parts[0] if len(address_parts) > 0 else ''
                city = address_parts[1] if len(address_parts) > 1 else ''
                state_zip = address_parts[2] if len(address_parts) > 2 else ''
                state = state_zip.split()[0] if state_zip else ''
                zip_code = state_zip.split()[1] if len(state_zip.split()) > 1 else ''
            else:
                # Structured address
                street_address = address_info.get('streetAddress', '')
                city = address_info.get('addressLocality', '')
                state = address_info.get('addressRegion', '')
                zip_code = address_info.get('postalCode', '')
            
            # Price
            offers = data.get('offers', {})
            price = None
            if isinstance(offers, dict):
                price = self._clean_price(str(offers.get('price', '')))
            elif isinstance(offers, list) and offers:
                price = self._clean_price(str(offers[0].get('price', '')))
            
            # Property details - these might be in different locations
            bedrooms = None
            bathrooms = None
            square_feet = None
            
            # Check for additional properties
            additional_props = data.get('additionalProperty', [])
            for prop in additional_props:
                prop_name = prop.get('name', '').lower()
                prop_value = prop.get('value')
                
                if 'bedroom' in prop_name:
                    bedrooms = self._clean_number(str(prop_value))
                elif 'bathroom' in prop_name:
                    bathrooms = self._clean_number(str(prop_value))
                elif 'square' in prop_name or 'sqft' in prop_name:
                    square_feet = self._clean_number(str(prop_value))
            
            # URL
            listing_url = data.get('url', '')
            if listing_url and not listing_url.startswith('http'):
                listing_url = self.BASE_URL + listing_url
            
            # Create property object
            property_obj = Property(
                address=street_address,
                city=city,
                state=state,
                zip_code=zip_code,
                price=price,
                bedrooms=int(bedrooms) if bedrooms else None,
                bathrooms=float(bathrooms) if bathrooms else None,
                square_feet=int(square_feet) if square_feet else None,
                listing_url=listing_url
            )
            
            return property_obj
        
        except Exception as e:
            self.logger.warning(f"Error parsing structured data: {str(e)}")
            return None
    
    def _parse_card_html(self, card) -> Optional[Property]:
        """Parse property data from HTML card element."""
        try:
            # Address
            address_elem = card.find('div', {'data-testid': 'property-address'})
            if not address_elem:
                address_elem = card.find(class_=re.compile(r'address'))
            
            address = address_elem.get_text().strip() if address_elem else ''
            
            # Split address into components
            address_parts = address.split(', ') if address else []
            street_address = address_parts[0] if len(address_parts) > 0 else ''
            city = address_parts[1] if len(address_parts) > 1 else ''
            state_zip = address_parts[2] if len(address_parts) > 2 else ''
            
            state = ''
            zip_code = ''
            if state_zip:
                parts = state_zip.split()
                if len(parts) >= 2:
                    state = parts[0]
                    zip_code = parts[1]
            
            # Price
            price_elem = card.find('span', {'data-testid': 'property-price'})
            if not price_elem:
                price_elem = card.find(class_=re.compile(r'price'))
            price = self._clean_price(price_elem.get_text()) if price_elem else None
            
            # Property details
            details_elem = card.find('ul', {'data-testid': 'property-meta'})
            if not details_elem:
                details_elem = card.find(class_=re.compile(r'property-meta'))
            
            bedrooms = bathrooms = square_feet = None
            
            if details_elem:
                details_text = details_elem.get_text()
                # Parse bedrooms, bathrooms, sqft
                bed_match = re.search(r'(\d+)\s*bed', details_text, re.IGNORECASE)
                bath_match = re.search(r'(\d+(?:\.\d+)?)\s*bath', details_text, re.IGNORECASE)
                sqft_match = re.search(r'([\d,]+)\s*sqft', details_text, re.IGNORECASE)
                
                bedrooms = int(bed_match.group(1)) if bed_match else None
                bathrooms = float(bath_match.group(1)) if bath_match else None
                square_feet = int(sqft_match.group(1).replace(',', '')) if sqft_match else None
            
            # URL
            link_elem = card.find('a')
            listing_url = None
            if link_elem and link_elem.get('href'):
                href = link_elem['href']
                listing_url = href if href.startswith('http') else self.BASE_URL + href
            
            # Create property object
            property_obj = Property(
                address=street_address,
                city=city,
                state=state,
                zip_code=zip_code,
                price=price,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                square_feet=square_feet,
                listing_url=listing_url
            )
            
            return property_obj
        
        except Exception as e:
            self.logger.warning(f"Error parsing card HTML: {str(e)}")
            return None
    
    def _extract_property_details(self, soup, property_url: str) -> Optional[Property]:
        """Extract detailed property information from a property page."""
        try:
            # Look for structured data first
            script_tags = soup.find_all('script', type='application/ld+json')
            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get('@type') == 'Product':
                        return self._parse_structured_data(data)
                    elif isinstance(data, list):
                        for item in data:
                            if item.get('@type') == 'Product':
                                return self._parse_structured_data(item)
                except Exception as e:
                    continue
            
            # Fallback to HTML parsing
            return self._parse_property_details_from_html(soup, property_url)
        
        except Exception as e:
            self.logger.error(f"Error extracting property details: {str(e)}")
            return None
    
    def _parse_property_details_from_html(self, soup, property_url: str) -> Optional[Property]:
        """Parse detailed property data from HTML (fallback method)."""
        try:
            # This would contain more comprehensive HTML parsing
            # For now, return a basic implementation
            
            # Try to extract basic info from meta tags or data attributes
            address_elem = soup.find('h1', class_=re.compile(r'address'))
            address = address_elem.get_text().strip() if address_elem else ''
            
            # Price
            price_elem = soup.find(class_=re.compile(r'price'))
            price = self._clean_price(price_elem.get_text()) if price_elem else None
            
            # Property details
            beds_elem = soup.find(text=re.compile(r'(\d+)\s*bed', re.IGNORECASE))
            baths_elem = soup.find(text=re.compile(r'(\d+(?:\.\d+)?)\s*bath', re.IGNORECASE))
            sqft_elem = soup.find(text=re.compile(r'([\d,]+)\s*sq\s*ft', re.IGNORECASE))
            
            bedrooms = None
            bathrooms = None
            square_feet = None
            
            if beds_elem:
                bed_match = re.search(r'(\d+)', beds_elem)
                bedrooms = int(bed_match.group(1)) if bed_match else None
            
            if baths_elem:
                bath_match = re.search(r'(\d+(?:\.\d+)?)', baths_elem)
                bathrooms = float(bath_match.group(1)) if bath_match else None
            
            if sqft_elem:
                sqft_match = re.search(r'([\d,]+)', sqft_elem)
                square_feet = int(sqft_match.group(1).replace(',', '')) if sqft_match else None
            
            # Parse address components
            address_parts = address.split(', ') if address else []
            street_address = address_parts[0] if len(address_parts) > 0 else ''
            city = address_parts[1] if len(address_parts) > 1 else ''
            state_zip = address_parts[2] if len(address_parts) > 2 else ''
            
            state = ''
            zip_code = ''
            if state_zip:
                parts = state_zip.split()
                if len(parts) >= 2:
                    state = parts[0]
                    zip_code = parts[1]
            
            # Create property object
            property_obj = Property(
                address=street_address,
                city=city,
                state=state,
                zip_code=zip_code,
                price=price,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                square_feet=square_feet,
                listing_url=property_url
            )
            
            return property_obj
        
        except Exception as e:
            self.logger.warning(f"Error parsing property details from HTML: {str(e)}")
            return None