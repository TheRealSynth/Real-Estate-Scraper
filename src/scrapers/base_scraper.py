"""Base scraper class with common functionality."""

import time
import random
import asyncio
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime

import requests
import aiohttp
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent
from webdriver_manager.chrome import ChromeDriverManager

from ..utils.config import ScraperConfig
from ..utils.logger import setup_logger


@dataclass
class Property:
    """Data class for property information."""
    
    address: str
    city: str
    state: str
    zip_code: str
    price: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[int] = None
    lot_size: Optional[float] = None
    property_type: Optional[str] = None
    year_built: Optional[int] = None
    listing_date: Optional[datetime] = None
    listing_url: Optional[str] = None
    listing_agent: Optional[str] = None
    description: Optional[str] = None
    photos: List[str] = None
    features: List[str] = None
    scraped_at: datetime = None
    
    def __post_init__(self):
        if self.photos is None:
            self.photos = []
        if self.features is None:
            self.features = []
        if self.scraped_at is None:
            self.scraped_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert property to dictionary."""
        data = asdict(self)
        # Convert datetime objects to strings
        if data['listing_date']:
            data['listing_date'] = data['listing_date'].isoformat()
        if data['scraped_at']:
            data['scraped_at'] = data['scraped_at'].isoformat()
        return data


class BaseScraper(ABC):
    """Base class for all real estate scrapers."""
    
    def __init__(self, config: ScraperConfig):
        self.config = config
        self.logger = setup_logger(
            f"{self.__class__.__name__}",
            level=config.log_level,
            log_file=f"logs/{self.__class__.__name__.lower()}.log"
        )
        self.session = requests.Session()
        self.user_agent = UserAgent() if config.user_agent_rotate else None
        self._setup_session()
    
    def _setup_session(self):
        """Set up the requests session with headers."""
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        }
        
        if self.user_agent:
            headers['User-Agent'] = self.user_agent.random
        else:
            headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        
        self.session.headers.update(headers)
    
    def _get_page(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """Get and parse a web page with retries."""
        for attempt in range(retries):
            try:
                # Rotate user agent if enabled
                if self.user_agent and self.config.user_agent_rotate:
                    self.session.headers['User-Agent'] = self.user_agent.random
                
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Add delay between requests
                time.sleep(self.config.scraper_delay + random.uniform(0, 1))
                
                return soup
                
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    self.logger.error(f"Failed to fetch {url} after {retries} attempts")
                    return None
    
    def _get_selenium_driver(self) -> webdriver.Chrome:
        """Create and configure a Selenium Chrome driver."""
        chrome_options = Options()
        
        if self.config.headless_browser:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # User agent
        if self.user_agent and self.config.user_agent_rotate:
            chrome_options.add_argument(f'--user-agent={self.user_agent.random}')
        
        driver = webdriver.Chrome(
            ChromeDriverManager().install(),
            options=chrome_options
        )
        
        return driver
    
    async def _get_page_async(self, session: aiohttp.ClientSession, url: str) -> Optional[BeautifulSoup]:
        """Asynchronously get and parse a web page."""
        try:
            headers = {}
            if self.user_agent and self.config.user_agent_rotate:
                headers['User-Agent'] = self.user_agent.random
            
            async with session.get(url, headers=headers, timeout=30) as response:
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Add async delay
                await asyncio.sleep(self.config.scraper_delay)
                
                return soup
                
        except Exception as e:
            self.logger.error(f"Failed to fetch {url}: {str(e)}")
            return None
    
    @abstractmethod
    def scrape_listings(self, search_params: Dict[str, Any]) -> List[Property]:
        """Scrape property listings based on search parameters."""
        pass
    
    @abstractmethod
    def scrape_property_details(self, property_url: str) -> Optional[Property]:
        """Scrape detailed information for a specific property."""
        pass
    
    def _clean_price(self, price_text: str) -> Optional[float]:
        """Extract and clean price from text."""
        if not price_text:
            return None
        
        # Remove common currency symbols and text
        cleaned = price_text.replace('$', '').replace(',', '').replace(' ', '')
        cleaned = cleaned.split('/')[0]  # Remove '/month' etc.
        
        try:
            return float(cleaned)
        except ValueError:
            return None
    
    def _clean_number(self, number_text: str) -> Optional[Union[int, float]]:
        """Extract and clean numbers from text."""
        if not number_text:
            return None
        
        # Extract numbers from text
        import re
        numbers = re.findall(r'[\d.]+', number_text.replace(',', ''))
        
        if numbers:
            try:
                num = float(numbers[0])
                return int(num) if num.is_integer() else num
            except ValueError:
                return None
        
        return None
    
    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """Parse date from various text formats."""
        if not date_text:
            return None
        
        import re
        from dateutil import parser
        
        try:
            # Clean the date text
            cleaned = re.sub(r'[^\w\s/.-]', '', date_text.strip())
            return parser.parse(cleaned)
        except Exception:
            return None