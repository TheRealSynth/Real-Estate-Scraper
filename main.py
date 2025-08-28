#!/usr/bin/env python3
"""
Real Estate Scraper - Main Application
"""
import sys
import argparse
import logging
from typing import List

from src.models import SearchCriteria, Property
from src.data_manager import DataManager
from scrapers.zillow_scraper import ZillowScraper
from scrapers.realtor_scraper import RealtorScraper
from config.settings import *

def setup_logging():
    """Setup logging configuration"""
    import os
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )

def get_available_scrapers():
    """Get dictionary of available scrapers"""
    return {
        'zillow': ZillowScraper,
        'realtor': RealtorScraper,
    }

def scrape_properties(criteria: SearchCriteria, scrapers: List[str] = None) -> List[Property]:
    """Scrape properties using specified scrapers"""
    all_properties = []
    available_scrapers = get_available_scrapers()
    
    if not scrapers:
        scrapers = list(available_scrapers.keys())
    
    logger = logging.getLogger(__name__)
    
    for scraper_name in scrapers:
        if scraper_name not in available_scrapers:
            logger.warning(f"Unknown scraper: {scraper_name}")
            continue
        
        logger.info(f"Starting {scraper_name} scraper...")
        
        try:
            scraper_class = available_scrapers[scraper_name]
            with scraper_class(use_selenium=True) as scraper:
                properties = scraper.scrape_property_list(criteria)
                all_properties.extend(properties)
                logger.info(f"{scraper_name} scraped {len(properties)} properties")
                
        except Exception as e:
            logger.error(f"Error with {scraper_name} scraper: {str(e)}")
    
    return all_properties

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description='Real Estate Scraper')
    parser.add_argument('location', help='Location to search (e.g., "New York, NY")')
    parser.add_argument('--min-price', type=float, help='Minimum price filter')
    parser.add_argument('--max-price', type=float, help='Maximum price filter')
    parser.add_argument('--min-bedrooms', type=int, help='Minimum bedrooms')
    parser.add_argument('--max-bedrooms', type=int, help='Maximum bedrooms')
    parser.add_argument('--min-bathrooms', type=float, help='Minimum bathrooms')
    parser.add_argument('--max-bathrooms', type=float, help='Maximum bathrooms')
    parser.add_argument('--property-types', nargs='+', 
                       choices=['house', 'condo', 'townhouse'], 
                       help='Property types to include')
    parser.add_argument('--max-pages', type=int, default=5, 
                       help='Maximum pages to scrape per site')
    parser.add_argument('--scrapers', nargs='+', 
                       choices=['zillow', 'realtor'], 
                       help='Scrapers to use (default: all)')
    parser.add_argument('--output-format', choices=['csv', 'json', 'database'],
                       default=OUTPUT_FORMAT, help='Output format')
    parser.add_argument('--output-prefix', default='properties',
                       help='Output file prefix')
    parser.add_argument('--stats', action='store_true',
                       help='Show statistics of existing data')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    if args.verbose:
        global LOG_LEVEL
        LOG_LEVEL = 'DEBUG'
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Show statistics if requested
    if args.stats:
        data_manager = DataManager()
        stats = data_manager.get_property_statistics()
        
        print("\n=== Property Database Statistics ===")
        print(f"Total Properties: {stats.get('total_properties', 0)}")
        print(f"Average Price: ${stats.get('average_price', 0):,.2f}")
        
        price_range = stats.get('price_range', {})
        if price_range.get('min') and price_range.get('max'):
            print(f"Price Range: ${price_range['min']:,.2f} - ${price_range['max']:,.2f}")
        
        sources = stats.get('sources', {})
        if sources:
            print("\nProperties by Source:")
            for source, count in sources.items():
                print(f"  {source}: {count}")
        
        types = stats.get('property_types', {})
        if types:
            print("\nProperties by Type:")
            for prop_type, count in types.items():
                print(f"  {prop_type}: {count}")
        
        return
    
    # Create search criteria
    criteria = SearchCriteria(
        location=args.location,
        min_price=args.min_price,
        max_price=args.max_price,
        min_bedrooms=args.min_bedrooms,
        max_bedrooms=args.max_bedrooms,
        min_bathrooms=args.min_bathrooms,
        max_bathrooms=args.max_bathrooms,
        property_types=args.property_types or [],
        max_pages=args.max_pages
    )
    
    logger.info(f"Starting scrape for location: {criteria.location}")
    logger.info(f"Search criteria: {criteria}")
    
    # Scrape properties
    properties = scrape_properties(criteria, args.scrapers)
    
    if not properties:
        logger.warning("No properties found!")
        return
    
    logger.info(f"Total properties scraped: {len(properties)}")
    
    # Save properties
    data_manager = DataManager()
    
    # Override output format if specified
    if args.output_format != OUTPUT_FORMAT:
        import config.settings as settings
        settings.OUTPUT_FORMAT = args.output_format
    
    saved_file = data_manager.save_properties(properties, args.output_prefix)
    
    if saved_file:
        print(f"\n✅ Successfully scraped {len(properties)} properties!")
        print(f"📁 Data saved to: {saved_file}")
        
        # Show sample properties
        print(f"\n📋 Sample Properties:")
        for i, prop in enumerate(properties[:5]):
            print(f"{i+1}. {prop.address} - ${prop.price:,.2f}" if prop.price else f"{i+1}. {prop.address} - Price not available")
        
        if len(properties) > 5:
            print(f"... and {len(properties) - 5} more properties")
    else:
        logger.error("Failed to save properties")

if __name__ == "__main__":
    main()