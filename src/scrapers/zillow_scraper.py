"""Zillow real estate scraper."""

import re
import json
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, urlparse, parse_qs

from .base_scraper import BaseScraper, Property


class ZillowScraper(BaseScraper):
    """Scraper for Zillow real estate listings."""
    
    BASE_URL = "https://www.zillow.com"
    SEARCH_URL = "https://www.zillow.com/homes"
    
    def __init__(self, config):
        super().__init__(config)
        self.logger.info("Initialized Zillow scraper")
    
    def scrape_listings(self, search_params: Dict[str, Any]) -> List[Property]:
        """
        Scrape Zillow listings based on search parameters.
        
        Args:
            search_params: Dictionary containing search criteria like:
                - location (str): City, state, or zip code
                - min_price (int): Minimum price
                - max_price (int): Maximum price
                - bedrooms (int): Number of bedrooms
                - bathrooms (int): Number of bathrooms
                - property_type (str): home_type (houses, condos, etc.)
        """
        properties = []
        
        # Build search URL
        search_url = self._build_search_url(search_params)
        self.logger.info(f"Searching Zillow with URL: {search_url}")
        
        try:
            soup = self._get_page(search_url)
            if not soup:
                return properties
            
            # Extract property listings from the page
            listings = self._extract_listings_from_page(soup)
            properties.extend(listings)
            
            # Handle pagination
            page = 1
            while page < 10:  # Limit to 10 pages to prevent infinite loops
                page += 1
                next_url = self._get_next_page_url(search_url, page)
                
                if not next_url:
                    break
                
                soup = self._get_page(next_url)
                if not soup:
                    break
                
                page_listings = self._extract_listings_from_page(soup)
                if not page_listings:
                    break
                
                properties.extend(page_listings)
                self.logger.info(f"Scraped page {page}, found {len(page_listings)} listings")
        
        except Exception as e:
            self.logger.error(f"Error scraping Zillow listings: {str(e)}")
        
        self.logger.info(f"Total properties found: {len(properties)}")
        return properties
    
    def scrape_property_details(self, property_url: str) -> Optional[Property]:
        """Scrape detailed information for a specific Zillow property."""
        try:
            soup = self._get_page(property_url)
            if not soup:
                return None
            
            return self._extract_property_details(soup, property_url)
        
        except Exception as e:
            self.logger.error(f"Error scraping property details from {property_url}: {str(e)}")
            return None
    
    def _build_search_url(self, search_params: Dict[str, Any]) -> str:
        """Build Zillow search URL from parameters."""
        params = {}
        
        # Location
        if 'location' in search_params:
            params['searchQueryState'] = json.dumps({
                "pagination": {},
                "usersSearchTerm": search_params['location'],
                "mapBounds": {},
                "regionSelection": [
                    {
                        "regionId": None,
                        "regionType": 6
                    }
                ],
                "isMapVisible": True,
                "filterState": {
                    "price": {},
                    "beds": {},
                    "baths": {},
                    "sqft": {},
                    "lot": {},
                    "built": {},
                    "ah": {"value": True}
                },
                "isListVisible": True
            })
        
        # Price range
        filter_state = {}
        if 'min_price' in search_params or 'max_price' in search_params:
            price_filter = {}
            if 'min_price' in search_params:
                price_filter['min'] = search_params['min_price']
            if 'max_price' in search_params:
                price_filter['max'] = search_params['max_price']
            filter_state['price'] = price_filter
        
        # Bedrooms
        if 'bedrooms' in search_params:
            filter_state['beds'] = {'min': search_params['bedrooms']}
        
        # Bathrooms
        if 'bathrooms' in search_params:
            filter_state['baths'] = {'min': search_params['bathrooms']}
        
        if filter_state and 'searchQueryState' in params:
            query_state = json.loads(params['searchQueryState'])
            query_state['filterState'].update(filter_state)
            params['searchQueryState'] = json.dumps(query_state)
        
        return f"{self.SEARCH_URL}/?{urlencode(params)}"
    
    def _extract_listings_from_page(self, soup) -> List[Property]:
        """Extract property listings from a Zillow search results page."""
        properties = []
        
        # Try to find script tag with property data
        script_tags = soup.find_all('script', {'id': '__NEXT_DATA__'})
        if script_tags:
            try:
                data = json.loads(script_tags[0].string)
                search_results = self._extract_from_next_data(data)
                properties.extend(search_results)
            except Exception as e:
                self.logger.warning(f"Could not parse __NEXT_DATA__: {str(e)}")
        
        # Fallback to HTML parsing
        if not properties:
            properties = self._extract_from_html(soup)
        
        return properties
    
    def _extract_from_next_data(self, data: dict) -> List[Property]:
        """Extract properties from Next.js data structure."""
        properties = []
        
        try:
            props = data.get('props', {}).get('pageProps', {})
            search_results = props.get('searchPageState', {}).get('cat1', {}).get('searchResults', {})
            listings = search_results.get('listResults', [])
            
            for listing in listings:
                prop = self._parse_listing_data(listing)
                if prop:
                    properties.append(prop)
        
        except Exception as e:
            self.logger.warning(f"Error parsing Next.js data: {str(e)}")
        
        return properties
    
    def _extract_from_html(self, soup) -> List[Property]:
        """Extract properties from HTML elements (fallback method)."""
        properties = []
        
        # Look for property cards
        cards = soup.find_all('article', {'data-test': 'property-card'})
        if not cards:
            cards = soup.find_all('div', class_=re.compile(r'list-card'))
        
        for card in cards:
            try:
                prop = self._parse_card_html(card)
                if prop:
                    properties.append(prop)
            except Exception as e:
                self.logger.warning(f"Error parsing property card: {str(e)}")
        
        return properties
    
    def _parse_listing_data(self, listing: dict) -> Optional[Property]:
        """Parse property data from Zillow API response."""
        try:
            # Extract basic info
            address_parts = listing.get('address', {})
            address = address_parts.get('streetAddress', '')
            city = address_parts.get('city', '')
            state = address_parts.get('state', '')
            zip_code = address_parts.get('zipcode', '')
            
            # Price
            price = listing.get('price')
            if isinstance(price, str):
                price = self._clean_price(price)
            
            # Property details
            bedrooms = listing.get('beds')
            bathrooms = listing.get('baths')
            square_feet = listing.get('area')
            lot_size = listing.get('lotAreaValue')
            
            # Property type and year
            property_type = listing.get('homeType')
            year_built = listing.get('yearBuilt')
            
            # URLs and agent info
            listing_url = listing.get('detailUrl')
            if listing_url and not listing_url.startswith('http'):
                listing_url = self.BASE_URL + listing_url
            
            # Photos
            photos = []
            if 'imgSrc' in listing:
                photos.append(listing['imgSrc'])
            
            # Create property object
            property_obj = Property(
                address=address,
                city=city,
                state=state,
                zip_code=zip_code,
                price=price,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                square_feet=square_feet,
                lot_size=lot_size,
                property_type=property_type,
                year_built=year_built,
                listing_url=listing_url,
                photos=photos
            )
            
            return property_obj
        
        except Exception as e:
            self.logger.warning(f"Error parsing listing data: {str(e)}")
            return None
    
    def _parse_card_html(self, card) -> Optional[Property]:
        """Parse property data from HTML card element."""
        try:
            # Address
            address_elem = card.find('address')
            address = address_elem.get_text().strip() if address_elem else ''
            
            # Split address into components (basic parsing)
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
            price_elem = card.find('span', {'data-test': 'property-card-price'})
            if not price_elem:
                price_elem = card.find(class_=re.compile(r'price'))
            price = self._clean_price(price_elem.get_text()) if price_elem else None
            
            # Property details
            details_elem = card.find('ul', {'data-test': 'property-card-details'})
            bedrooms = bathrooms = square_feet = None
            
            if details_elem:
                details_text = details_elem.get_text()
                # Parse bedrooms, bathrooms, sqft
                bed_match = re.search(r'(\d+)\s*bd', details_text)
                bath_match = re.search(r'(\d+(?:\.\d+)?)\s*ba', details_text)
                sqft_match = re.search(r'([\d,]+)\s*sqft', details_text)
                
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
            # Try to get data from Next.js data
            script_tags = soup.find_all('script', {'id': '__NEXT_DATA__'})
            if script_tags:
                try:
                    data = json.loads(script_tags[0].string)
                    return self._parse_property_details_from_data(data, property_url)
                except Exception as e:
                    self.logger.warning(f"Could not parse property __NEXT_DATA__: {str(e)}")
            
            # Fallback to HTML parsing
            return self._parse_property_details_from_html(soup, property_url)
        
        except Exception as e:
            self.logger.error(f"Error extracting property details: {str(e)}")
            return None
    
    def _parse_property_details_from_data(self, data: dict, property_url: str) -> Optional[Property]:
        """Parse detailed property data from Next.js data structure."""
        # Implementation would be similar to _parse_listing_data but more comprehensive
        # This is a simplified version
        return None
    
    def _parse_property_details_from_html(self, soup, property_url: str) -> Optional[Property]:
        """Parse detailed property data from HTML (fallback method)."""
        # Implementation would parse HTML elements for detailed property info
        # This is a simplified version
        return None
    
    def _get_next_page_url(self, base_url: str, page: int) -> Optional[str]:
        """Generate URL for the next page of results."""
        try:
            parsed = urlparse(base_url)
            query_params = parse_qs(parsed.query)
            
            if 'searchQueryState' in query_params:
                query_state = json.loads(query_params['searchQueryState'][0])
                query_state['pagination'] = {'currentPage': page}
                
                new_params = query_params.copy()
                new_params['searchQueryState'] = [json.dumps(query_state)]
                
                return f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urlencode(new_params, doseq=True)}"
        
        except Exception as e:
            self.logger.warning(f"Error building next page URL: {str(e)}")
        
        return None