"""
Configuration settings for the Real Estate Scraper
"""
import os
from dotenv import load_dotenv

load_dotenv()

# General settings
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
REQUEST_DELAY = 2  # Delay between requests in seconds
MAX_RETRIES = 3
TIMEOUT = 30

# Database settings
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/properties.db')

# Output settings
OUTPUT_FORMAT = 'csv'  # Options: 'csv', 'json', 'database'
OUTPUT_DIR = 'data'

# Scraping settings
MAX_PAGES = 50  # Maximum number of pages to scrape per search
MAX_PROPERTIES = 1000  # Maximum number of properties to scrape

# Selenium settings
HEADLESS = True
BROWSER = 'chrome'  # Options: 'chrome', 'firefox'

# Rate limiting
REQUESTS_PER_MINUTE = 30

# Logging settings
LOG_LEVEL = 'INFO'
LOG_FILE = 'logs/scraper.log'