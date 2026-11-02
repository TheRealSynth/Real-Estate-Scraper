"""Configuration management for the real estate scraper."""

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from pydantic import BaseModel, Field


class ScraperConfig(BaseModel):
    """Configuration model for the scraper."""
    
    scraper_delay: float = Field(default=2.0, description="Delay between requests in seconds")
    max_concurrent_requests: int = Field(default=3, description="Maximum concurrent requests")
    user_agent_rotate: bool = Field(default=True, description="Whether to rotate user agents")
    headless_browser: bool = Field(default=True, description="Run browser in headless mode")
    log_level: str = Field(default="INFO", description="Logging level")
    output_format: str = Field(default="csv", description="Output format (csv, json, db)")
    output_dir: str = Field(default="./data", description="Output directory")
    database_url: str = Field(default="sqlite:///real_estate.db", description="Database URL")
    
    # API Keys
    zillow_api_key: Optional[str] = Field(default=None, description="Zillow API key")
    realtor_api_key: Optional[str] = Field(default=None, description="Realtor.com API key")


def load_config() -> ScraperConfig:
    """Load configuration from environment variables."""
    load_dotenv()
    
    config_dict = {
        "scraper_delay": float(os.getenv("SCRAPER_DELAY", "2.0")),
        "max_concurrent_requests": int(os.getenv("MAX_CONCURRENT_REQUESTS", "3")),
        "user_agent_rotate": os.getenv("USER_AGENT_ROTATE", "true").lower() == "true",
        "headless_browser": os.getenv("HEADLESS_BROWSER", "true").lower() == "true",
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "output_format": os.getenv("OUTPUT_FORMAT", "csv"),
        "output_dir": os.getenv("OUTPUT_DIR", "./data"),
        "database_url": os.getenv("DATABASE_URL", "sqlite:///real_estate.db"),
        "zillow_api_key": os.getenv("ZILLOW_API_KEY"),
        "realtor_api_key": os.getenv("REALTOR_API_KEY"),
    }
    
    return ScraperConfig(**config_dict)