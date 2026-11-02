"""
Base scraper class with common functionality
"""
import time
import logging
import requests
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from fake_useragent import UserAgent
from bs4 import BeautifulSoup

from .models import Property, SearchCriteria
from config.settings import *

class BaseScraper(ABC):
    """Base class for all property scrapers"""
    
    def __init__(self, use_selenium: bool = False):
        self.use_selenium = use_selenium
        self.session = None
        self.driver = None
        self.ua = UserAgent()
        self.logger = self._setup_logging()
        
        if not use_selenium:
            self._setup_session()
        else:
            self._setup_selenium()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(getattr(logging, LOG_LEVEL))
        
        if not logger.handlers:
            # Create logs directory if it doesn't exist
            import os
            os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
            
            # File handler
            file_handler = logging.FileHandler(LOG_FILE)
            file_handler.setLevel(getattr(logging, LOG_LEVEL))
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # Formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        
        return logger
    
    def _setup_session(self):
        """Setup requests session with headers and retries"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def _setup_selenium(self):
        """Setup Selenium WebDriver"""
        if BROWSER.lower() == 'chrome':
            options = ChromeOptions()
            if HEADLESS:
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument(f'--user-agent={self.ua.random}')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            
            self.driver = webdriver.Chrome(
                service=webdriver.chrome.service.Service(ChromeDriverManager().install()),
                options=options
            )
        elif BROWSER.lower() == 'firefox':
            options = FirefoxOptions()
            if HEADLESS:
                options.add_argument('--headless')
            options.set_preference("general.useragent.override", self.ua.random)
            
            self.driver = webdriver.Firefox(
                service=webdriver.firefox.service.Service(GeckoDriverManager().install()),
                options=options
            )
        
        if self.driver:
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(TIMEOUT)
    
    def get_page(self, url: str, retries: int = MAX_RETRIES) -> Optional[BeautifulSoup]:
        """Get page content using requests or Selenium"""
        for attempt in range(retries):
            try:
                if self.use_selenium and self.driver:
                    self.driver.get(url)
                    time.sleep(REQUEST_DELAY)
                    return BeautifulSoup(self.driver.page_source, 'html.parser')
                else:
                    response = self.session.get(url, timeout=TIMEOUT)
                    response.raise_for_status()
                    time.sleep(REQUEST_DELAY)
                    return BeautifulSoup(response.content, 'html.parser')
                    
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt < retries - 1:
                    time.sleep(REQUEST_DELAY * 2)
                else:
                    self.logger.error(f"Failed to get page {url} after {retries} attempts")
                    return None
    
    def wait_for_element(self, by: By, value: str, timeout: int = 10):
        """Wait for element to be present (Selenium only)"""
        if self.driver:
            try:
                return WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, value))
                )
            except TimeoutException:
                self.logger.warning(f"Element {value} not found within {timeout} seconds")
                return None
        return None
    
    def click_element(self, by: By, value: str, timeout: int = 10) -> bool:
        """Click element (Selenium only)"""
        if self.driver:
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((by, value))
                )
                element.click()
                return True
            except TimeoutException:
                self.logger.warning(f"Element {value} not clickable within {timeout} seconds")
                return False
        return False
    
    def extract_text(self, soup: BeautifulSoup, selector: str, default: str = None) -> Optional[str]:
        """Extract text from soup using CSS selector"""
        try:
            element = soup.select_one(selector)
            return element.get_text(strip=True) if element else default
        except Exception as e:
            self.logger.warning(f"Error extracting text with selector {selector}: {str(e)}")
            return default
    
    def extract_number(self, text: str) -> Optional[float]:
        """Extract number from text string"""
        if not text:
            return None
        
        import re
        # Remove commas and extract number
        text = re.sub(r'[^\d.,]', '', text)
        text = text.replace(',', '')
        
        try:
            return float(text)
        except ValueError:
            return None
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        import re
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        return text
    
    @abstractmethod
    def build_search_url(self, criteria: SearchCriteria) -> str:
        """Build search URL based on criteria"""
        pass
    
    @abstractmethod
    def scrape_property_list(self, criteria: SearchCriteria) -> List[Property]:
        """Scrape property list based on search criteria"""
        pass
    
    @abstractmethod
    def scrape_property_details(self, property_url: str) -> Optional[Property]:
        """Scrape detailed property information"""
        pass
    
    def close(self):
        """Close connections and cleanup"""
        if self.driver:
            self.driver.quit()
        if self.session:
            self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()