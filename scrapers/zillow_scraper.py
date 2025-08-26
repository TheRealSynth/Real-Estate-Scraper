"""
Zillow property scraper
"""
import re
import time
import urllib.parse
from typing import List, Optional
from datetime import datetime

from src.base_scraper import BaseScraper
from src.models import Property, SearchCriteria

class ZillowScraper(BaseScraper):
    """Scraper for Zillow.com"""
    
    def __init__(self, use_selenium: bool = True):
        super().__init__(use_selenium=use_selenium)
        self.base_url = "https://www.zillow.com"
        self.search_url = "https://www.zillow.com/homes/"
    
    def build_search_url(self, criteria: SearchCriteria) -> str:
        """Build Zillow search URL"""
        # Format location for URL
        location = criteria.location.replace(' ', '-').replace(',', '')
        url = f"{self.search_url}{location}_rb/"
        
        # Add filters as query parameters
        params = {}
        
        if criteria.min_price:
            params['price_min'] = int(criteria.min_price)
        
        if criteria.max_price:
            params['price_max'] = int(criteria.max_price)
        
        if criteria.min_bedrooms:
            params['beds_min'] = criteria.min_bedrooms
        
        if criteria.max_bedrooms:
            params['beds_max'] = criteria.max_bedrooms
        
        if criteria.min_bathrooms:
            params['baths_min'] = criteria.min_bathrooms
        
        if criteria.max_bathrooms:
            params['baths_max'] = criteria.max_bathrooms
        
        if criteria.property_types:
            # Map to Zillow property types
            zillow_types = []
            for prop_type in criteria.property_types:
                if prop_type.lower() in ['house', 'single family']:
                    zillow_types.append('house')
                elif prop_type.lower() in ['condo', 'condominium']:
                    zillow_types.append('condo')
                elif prop_type.lower() in ['townhouse', 'townhome']:
                    zillow_types.append('townhouse')
            
            if zillow_types:
                params['home_type'] = ','.join(zillow_types)
        
        if params:
            url += '?' + urllib.parse.urlencode(params)
        
        return url
    
    def scrape_property_list(self, criteria: SearchCriteria) -> List[Property]:
        """Scrape property listings from Zillow search results"""
        properties = []
        url = self.build_search_url(criteria)
        max_pages = criteria.max_pages or 10
        
        self.logger.info(f"Starting Zillow scrape for: {criteria.location}")
        self.logger.info(f"Search URL: {url}")
        
        for page in range(1, max_pages + 1):
            page_url = f"{url}&p={page}" if '?' in url else f"{url}?p={page}"
            
            self.logger.info(f"Scraping page {page}: {page_url}")
            soup = self.get_page(page_url)
            
            if not soup:
                self.logger.error(f"Failed to get page {page}")
                break
            
            # Extract property cards
            property_cards = soup.find_all('article', {'data-test': 'property-card'})
            
            if not property_cards:
                # Try alternative selectors
                property_cards = soup.find_all('div', class_=re.compile(r'list-card'))
                
            if not property_cards:
                self.logger.warning(f"No property cards found on page {page}")
                break
            
            for card in property_cards:
                try:
                    property_data = self._extract_property_from_card(card)
                    if property_data:
                        properties.append(property_data)
                except Exception as e:
                    self.logger.error(f"Error extracting property: {str(e)}")
                    continue
            
            self.logger.info(f"Found {len(property_cards)} properties on page {page}")
            
            # Check if we've reached the limit
            if len(properties) >= 1000:  # Reasonable limit
                break
        
        self.logger.info(f"Total properties scraped: {len(properties)}")
        return properties
    
    def _extract_property_from_card(self, card) -> Optional[Property]:
        """Extract property data from a property card"""
        try:
            # Property URL
            link_elem = card.find('a', {'data-test': 'property-card-link'})
            if not link_elem:
                link_elem = card.find('a')
            
            property_url = None
            if link_elem and link_elem.get('href'):
                property_url = urllib.parse.urljoin(self.base_url, link_elem['href'])
            
            # Price
            price_elem = card.find('span', {'data-test': 'property-card-price'})
            if not price_elem:
                price_elem = card.find('div', class_=re.compile(r'price'))
            
            price = None
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price = self.extract_number(price_text)
            
            # Address
            address_elem = card.find('address', {'data-test': 'property-card-addr'})
            if not address_elem:
                address_elem = card.find('address')
            
            address = address_elem.get_text(strip=True) if address_elem else None
            
            # Property details (bedrooms, bathrooms, sqft)
            details_elem = card.find('ul', {'data-test': 'property-card-details'})
            if not details_elem:
                details_elem = card.find('ul', class_=re.compile(r'list-card-details'))
            
            bedrooms = None
            bathrooms = None
            square_feet = None
            
            if details_elem:
                details_text = details_elem.get_text()
                
                # Extract bedrooms
                bed_match = re.search(r'(\d+)\s*bd', details_text, re.IGNORECASE)
                if bed_match:
                    bedrooms = int(bed_match.group(1))
                
                # Extract bathrooms
                bath_match = re.search(r'(\d+(?:\.\d+)?)\s*ba', details_text, re.IGNORECASE)
                if bath_match:
                    bathrooms = float(bath_match.group(1))
                
                # Extract square feet
                sqft_match = re.search(r'([\d,]+)\s*sqft', details_text, re.IGNORECASE)
                if sqft_match:
                    square_feet = self.extract_number(sqft_match.group(1))
            
            # Property type
            property_type = "Unknown"
            if card.find(text=re.compile(r'Condo', re.IGNORECASE)):
                property_type = "Condo"
            elif card.find(text=re.compile(r'Townhouse', re.IGNORECASE)):
                property_type = "Townhouse"
            elif card.find(text=re.compile(r'House', re.IGNORECASE)):
                property_type = "House"
            
            # Create property object
            property_data = Property(
                title=address,
                price=price,
                address=address,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                square_feet=square_feet,
                property_type=property_type,
                source_url=property_url,
                source_website="Zillow",
                scraped_at=datetime.now()
            )
            
            return property_data
            
        except Exception as e:
            self.logger.error(f"Error extracting property from card: {str(e)}")
            return None
    
    def scrape_property_details(self, property_url: str) -> Optional[Property]:
        """Scrape detailed property information from Zillow property page"""
        soup = self.get_page(property_url)
        
        if not soup:
            return None
        
        try:
            # This would contain more detailed scraping logic
            # For now, returning a basic property object
            title = self.extract_text(soup, 'h1[data-test="property-title"]')
            price_text = self.extract_text(soup, 'span[data-test="price"]')
            price = self.extract_number(price_text) if price_text else None
            
            # Address parsing
            address = self.extract_text(soup, 'h1[data-test="property-title"]')
            
            # More detailed extraction would go here...
            
            return Property(
                title=title,
                price=price,
                address=address,
                source_url=property_url,
                source_website="Zillow",
                scraped_at=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Error scraping property details: {str(e)}")
            return None