"""
Realtor.com property scraper
"""
import re
import urllib.parse
from typing import List, Optional
from datetime import datetime

from src.base_scraper import BaseScraper
from src.models import Property, SearchCriteria

class RealtorScraper(BaseScraper):
    """Scraper for Realtor.com"""
    
    def __init__(self, use_selenium: bool = True):
        super().__init__(use_selenium=use_selenium)
        self.base_url = "https://www.realtor.com"
        self.search_url = "https://www.realtor.com/realestateandhomes-search"
    
    def build_search_url(self, criteria: SearchCriteria) -> str:
        """Build Realtor.com search URL"""
        # Format location for URL
        location = criteria.location.replace(' ', '%20')
        url = f"{self.search_url}/{location}"
        
        # Add filters as query parameters
        params = {}
        
        if criteria.min_price:
            params['price-min'] = int(criteria.min_price)
        
        if criteria.max_price:
            params['price-max'] = int(criteria.max_price)
        
        if criteria.min_bedrooms:
            params['beds-min'] = criteria.min_bedrooms
        
        if criteria.max_bedrooms:
            params['beds-max'] = criteria.max_bedrooms
        
        if criteria.min_bathrooms:
            params['baths-min'] = int(criteria.min_bathrooms)
        
        if criteria.max_bathrooms:
            params['baths-max'] = int(criteria.max_bathrooms)
        
        if criteria.property_types:
            # Map to Realtor.com property types
            realtor_types = []
            for prop_type in criteria.property_types:
                if prop_type.lower() in ['house', 'single family']:
                    realtor_types.append('single_family_home')
                elif prop_type.lower() in ['condo', 'condominium']:
                    realtor_types.append('condos')
                elif prop_type.lower() in ['townhouse', 'townhome']:
                    realtor_types.append('townhomes')
            
            if realtor_types:
                params['type'] = ','.join(realtor_types)
        
        if params:
            url += '?' + urllib.parse.urlencode(params)
        
        return url
    
    def scrape_property_list(self, criteria: SearchCriteria) -> List[Property]:
        """Scrape property listings from Realtor.com search results"""
        properties = []
        url = self.build_search_url(criteria)
        max_pages = criteria.max_pages or 10
        
        self.logger.info(f"Starting Realtor.com scrape for: {criteria.location}")
        self.logger.info(f"Search URL: {url}")
        
        for page in range(1, max_pages + 1):
            page_url = f"{url}&pg={page}" if '?' in url else f"{url}?pg={page}"
            
            self.logger.info(f"Scraping page {page}: {page_url}")
            soup = self.get_page(page_url)
            
            if not soup:
                self.logger.error(f"Failed to get page {page}")
                break
            
            # Extract property cards
            property_cards = soup.find_all('div', {'data-testid': 'property-card'})
            
            if not property_cards:
                # Try alternative selectors
                property_cards = soup.find_all('div', class_=re.compile(r'BasePropertyCard'))
                
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
            if len(properties) >= 1000:
                break
        
        self.logger.info(f"Total properties scraped: {len(properties)}")
        return properties
    
    def _extract_property_from_card(self, card) -> Optional[Property]:
        """Extract property data from a property card"""
        try:
            # Property URL
            link_elem = card.find('a')
            property_url = None
            if link_elem and link_elem.get('href'):
                property_url = urllib.parse.urljoin(self.base_url, link_elem['href'])
            
            # Price
            price_elem = card.find('div', {'data-testid': 'card-price'})
            if not price_elem:
                price_elem = card.find('span', class_=re.compile(r'price'))
            
            price = None
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price = self.extract_number(price_text)
            
            # Address
            address_elem = card.find('div', {'data-testid': 'card-address'})
            if not address_elem:
                address_elem = card.find('div', class_=re.compile(r'address'))
            
            address = address_elem.get_text(strip=True) if address_elem else None
            
            # Property details
            details_elem = card.find('ul', {'data-testid': 'property-meta'})
            if not details_elem:
                details_elem = card.find('ul', class_=re.compile(r'property-meta'))
            
            bedrooms = None
            bathrooms = None
            square_feet = None
            
            if details_elem:
                details_text = details_elem.get_text()
                
                # Extract bedrooms
                bed_match = re.search(r'(\d+)\s*bed', details_text, re.IGNORECASE)
                if bed_match:
                    bedrooms = int(bed_match.group(1))
                
                # Extract bathrooms
                bath_match = re.search(r'(\d+(?:\.\d+)?)\s*bath', details_text, re.IGNORECASE)
                if bath_match:
                    bathrooms = float(bath_match.group(1))
                
                # Extract square feet
                sqft_match = re.search(r'([\d,]+)\s*sqft', details_text, re.IGNORECASE)
                if sqft_match:
                    square_feet = self.extract_number(sqft_match.group(1))
            
            # Property type
            property_type = "Unknown"
            type_elem = card.find('div', {'data-testid': 'property-type'})
            if type_elem:
                property_type = type_elem.get_text(strip=True)
            
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
                source_website="Realtor.com",
                scraped_at=datetime.now()
            )
            
            return property_data
            
        except Exception as e:
            self.logger.error(f"Error extracting property from card: {str(e)}")
            return None
    
    def scrape_property_details(self, property_url: str) -> Optional[Property]:
        """Scrape detailed property information from Realtor.com property page"""
        soup = self.get_page(property_url)
        
        if not soup:
            return None
        
        try:
            # Extract detailed information
            title = self.extract_text(soup, 'h1[data-testid="property-title"]')
            price_text = self.extract_text(soup, 'div[data-testid="price"]')
            price = self.extract_number(price_text) if price_text else None
            
            # Address
            address = self.extract_text(soup, 'h1[data-testid="property-title"]')
            
            # Property details
            bedrooms_text = self.extract_text(soup, 'span[data-testid="meta-beds"]')
            bedrooms = int(bedrooms_text) if bedrooms_text and bedrooms_text.isdigit() else None
            
            bathrooms_text = self.extract_text(soup, 'span[data-testid="meta-baths"]')
            bathrooms = float(bathrooms_text) if bathrooms_text else None
            
            sqft_text = self.extract_text(soup, 'span[data-testid="meta-sqft"]')
            square_feet = self.extract_number(sqft_text) if sqft_text else None
            
            # Description
            description = self.extract_text(soup, 'div[data-testid="description"]')
            
            # Features
            features = []
            feature_elements = soup.find_all('li', {'data-testid': re.compile(r'feature')})
            for elem in feature_elements:
                feature_text = elem.get_text(strip=True)
                if feature_text:
                    features.append(feature_text)
            
            return Property(
                title=title,
                price=price,
                address=address,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                square_feet=square_feet,
                description=description,
                features=features,
                source_url=property_url,
                source_website="Realtor.com",
                scraped_at=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Error scraping property details: {str(e)}")
            return None