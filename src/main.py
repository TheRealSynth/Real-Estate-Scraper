"""Main CLI interface for the Real Estate Scraper."""

import click
import sys
from typing import Dict, Any, List

from .utils.config import load_config
from .utils.logger import setup_logger
from .utils.data_processor import DataProcessor
from .utils.output_handler import OutputHandler
from .scrapers.zillow_scraper import ZillowScraper
from .scrapers.realtor_scraper import RealtorScraper
from .scrapers.base_scraper import Property


class RealEstateScraper:
    """Main scraper orchestrator."""
    
    def __init__(self):
        self.config = load_config()
        self.logger = setup_logger("RealEstateScraper", level=self.config.log_level)
        self.data_processor = DataProcessor(self.config)
        self.output_handler = OutputHandler(self.config)
        
        # Initialize scrapers
        self.scrapers = {
            'zillow': ZillowScraper(self.config),
            'realtor': RealtorScraper(self.config),
        }
    
    def scrape_properties(self, search_params: Dict[str, Any], sites: List[str] = None) -> List[Property]:
        """Scrape properties from specified sites."""
        if sites is None:
            sites = list(self.scrapers.keys())
        
        all_properties = []
        
        for site in sites:
            if site not in self.scrapers:
                self.logger.warning(f"Unknown scraper site: {site}")
                continue
            
            self.logger.info(f"Scraping {site}...")
            try:
                scraper = self.scrapers[site]
                properties = scraper.scrape_listings(search_params)
                
                if properties:
                    self.logger.info(f"Found {len(properties)} properties from {site}")
                    all_properties.extend(properties)
                else:
                    self.logger.warning(f"No properties found from {site}")
                    
            except Exception as e:
                self.logger.error(f"Error scraping {site}: {str(e)}")
        
        return all_properties
    
    def process_and_save(self, properties: List[Property], filters: Dict[str, Any] = None) -> str:
        """Process, filter, and save properties."""
        if not properties:
            self.logger.warning("No properties to process")
            return ""
        
        # Process and clean data
        self.logger.info("Processing and cleaning data...")
        processed_properties = self.data_processor.process_properties(properties)
        
        # Remove duplicates
        self.logger.info("Removing duplicates...")
        deduplicated = self.data_processor.deduplicate_properties(processed_properties)
        
        # Apply filters if provided
        if filters:
            self.logger.info("Applying filters...")
            filtered = self.data_processor.filter_properties(deduplicated, filters)
        else:
            filtered = deduplicated
        
        if not filtered:
            self.logger.warning("No properties remain after processing and filtering")
            return ""
        
        # Save results
        self.logger.info(f"Saving {len(filtered)} properties...")
        output_file = self.output_handler.save_properties(filtered)
        
        # Generate summary report
        summary_file = self.output_handler.save_summary_report(filtered)
        
        self.logger.info(f"Scraping completed! Results saved to: {output_file}")
        self.logger.info(f"Summary report saved to: {summary_file}")
        
        return output_file


@click.group()
@click.version_option(version="1.0.0", prog_name="Real Estate Scraper")
@click.pass_context
def cli(ctx):
    """Real Estate Scraper - Scrape property listings from various real estate websites."""
    ctx.ensure_object(dict)


@cli.command()
@click.option('--location', '-l', required=True, help='Location to search (city, state, or zip code)')
@click.option('--sites', '-s', multiple=True, type=click.Choice(['zillow', 'realtor', 'all']), 
              default=['all'], help='Real estate sites to scrape')
@click.option('--min-price', type=int, help='Minimum price filter')
@click.option('--max-price', type=int, help='Maximum price filter')
@click.option('--bedrooms', type=int, help='Minimum number of bedrooms')
@click.option('--bathrooms', type=float, help='Minimum number of bathrooms')
@click.option('--property-type', type=click.Choice(['house', 'condo', 'townhouse', 'apartment']), 
              help='Property type filter')
@click.option('--min-sqft', type=int, help='Minimum square footage')
@click.option('--max-sqft', type=int, help='Maximum square footage')
@click.option('--output-format', type=click.Choice(['csv', 'json', 'excel', 'db']), 
              help='Output format (overrides config)')
@click.option('--output-dir', type=click.Path(), help='Output directory (overrides config)')
@click.option('--no-filter', is_flag=True, help='Skip additional filtering of results')
def scrape(location, sites, min_price, max_price, bedrooms, bathrooms, property_type, 
           min_sqft, max_sqft, output_format, output_dir, no_filter):
    """Scrape real estate listings from specified sites."""
    
    scraper = RealEstateScraper()
    
    # Override config if command line options provided
    if output_format:
        scraper.config.output_format = output_format
    if output_dir:
        scraper.config.output_dir = output_dir
    
    # Build search parameters
    search_params = {'location': location}
    
    if min_price:
        search_params['min_price'] = min_price
    if max_price:
        search_params['max_price'] = max_price
    if bedrooms:
        search_params['bedrooms'] = bedrooms
    if bathrooms:
        search_params['bathrooms'] = bathrooms
    if property_type:
        search_params['property_type'] = property_type
    
    # Determine which sites to scrape
    if 'all' in sites:
        sites_to_scrape = ['zillow', 'realtor']
    else:
        sites_to_scrape = list(sites)
    
    click.echo(f"🏠 Scraping real estate listings for: {location}")
    click.echo(f"📊 Sites: {', '.join(sites_to_scrape)}")
    click.echo(f"💾 Output format: {scraper.config.output_format}")
    click.echo(f"📁 Output directory: {scraper.config.output_dir}")
    click.echo()
    
    try:
        # Scrape properties
        properties = scraper.scrape_properties(search_params, sites_to_scrape)
        
        if not properties:
            click.echo("❌ No properties found!")
            sys.exit(1)
        
        click.echo(f"✅ Found {len(properties)} total properties")
        
        # Build filters for post-processing
        filters = {}
        if not no_filter:
            if min_price or max_price:
                if min_price:
                    filters['min_price'] = min_price
                if max_price:
                    filters['max_price'] = max_price
            
            if bedrooms:
                filters['min_bedrooms'] = bedrooms
            if bathrooms:
                filters['min_bathrooms'] = bathrooms
            if min_sqft:
                filters['min_sqft'] = min_sqft
            if max_sqft:
                filters['max_sqft'] = max_sqft
        
        # Process and save
        output_file = scraper.process_and_save(properties, filters)
        
        if output_file:
            click.echo(f"🎉 Results saved to: {output_file}")
        else:
            click.echo("❌ Failed to save results")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        sys.exit(1)


@cli.command()
@click.option('--input-file', '-i', required=True, type=click.Path(exists=True), 
              help='Input JSON file with property data')
@click.option('--output-format', type=click.Choice(['csv', 'json', 'excel', 'db']), 
              default='csv', help='Output format')
@click.option('--output-dir', type=click.Path(), help='Output directory')
@click.option('--min-price', type=int, help='Minimum price filter')
@click.option('--max-price', type=int, help='Maximum price filter')
@click.option('--bedrooms', type=int, help='Minimum number of bedrooms')
@click.option('--bathrooms', type=float, help='Minimum number of bathrooms')
@click.option('--states', multiple=True, help='Filter by states (e.g., CA, NY)')
@click.option('--cities', multiple=True, help='Filter by cities')
def convert(input_file, output_format, output_dir, min_price, max_price, 
            bedrooms, bathrooms, states, cities):
    """Convert and filter existing property data."""
    
    scraper = RealEstateScraper()
    
    # Override config
    scraper.config.output_format = output_format
    if output_dir:
        scraper.config.output_dir = output_dir
    
    click.echo(f"📂 Loading properties from: {input_file}")
    
    try:
        # Load properties
        properties = scraper.output_handler.load_properties_from_json(input_file)
        
        if not properties:
            click.echo("❌ No properties found in input file!")
            sys.exit(1)
        
        click.echo(f"✅ Loaded {len(properties)} properties")
        
        # Build filters
        filters = {}
        if min_price:
            filters['min_price'] = min_price
        if max_price:
            filters['max_price'] = max_price
        if bedrooms:
            filters['min_bedrooms'] = bedrooms
        if bathrooms:
            filters['min_bathrooms'] = bathrooms
        if states:
            filters['states'] = list(states)
        if cities:
            filters['cities'] = list(cities)
        
        # Process and save
        output_file = scraper.process_and_save(properties, filters)
        
        if output_file:
            click.echo(f"🎉 Converted data saved to: {output_file}")
        else:
            click.echo("❌ Failed to convert data")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        sys.exit(1)


@cli.command()
@click.option('--input-file', '-i', required=True, type=click.Path(exists=True),
              help='Input JSON file with property data')
def analyze(input_file):
    """Analyze property data and generate detailed statistics."""
    
    scraper = RealEstateScraper()
    
    click.echo(f"📊 Analyzing properties from: {input_file}")
    
    try:
        # Load properties
        properties = scraper.output_handler.load_properties_from_json(input_file)
        
        if not properties:
            click.echo("❌ No properties found in input file!")
            sys.exit(1)
        
        # Generate and save summary report
        summary_file = scraper.output_handler.save_summary_report(properties, "analysis")
        
        click.echo(f"✅ Analysis complete! Report saved to: {summary_file}")
        
        # Display basic stats
        total = len(properties)
        with_price = len([p for p in properties if p.price])
        avg_price = sum(p.price for p in properties if p.price) / with_price if with_price else 0
        
        click.echo()
        click.echo("📈 Quick Stats:")
        click.echo(f"  Total Properties: {total}")
        click.echo(f"  Properties with Price: {with_price}")
        if avg_price:
            click.echo(f"  Average Price: ${avg_price:,.2f}")
        
        # Top cities
        cities = {}
        for prop in properties:
            if prop.city:
                cities[prop.city] = cities.get(prop.city, 0) + 1
        
        if cities:
            top_cities = sorted(cities.items(), key=lambda x: x[1], reverse=True)[:5]
            click.echo(f"  Top Cities:")
            for city, count in top_cities:
                click.echo(f"    {city}: {count} properties")
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        sys.exit(1)


@cli.command()
def config():
    """Show current configuration."""
    
    try:
        config = load_config()
        
        click.echo("⚙️  Current Configuration:")
        click.echo(f"  Scraper Delay: {config.scraper_delay}s")
        click.echo(f"  Max Concurrent Requests: {config.max_concurrent_requests}")
        click.echo(f"  User Agent Rotation: {config.user_agent_rotate}")
        click.echo(f"  Headless Browser: {config.headless_browser}")
        click.echo(f"  Log Level: {config.log_level}")
        click.echo(f"  Output Format: {config.output_format}")
        click.echo(f"  Output Directory: {config.output_dir}")
        click.echo(f"  Database URL: {config.database_url}")
        
        if config.zillow_api_key:
            click.echo(f"  Zillow API Key: {'*' * 20}")
        if config.realtor_api_key:
            click.echo(f"  Realtor API Key: {'*' * 20}")
            
    except Exception as e:
        click.echo(f"❌ Error loading configuration: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    cli()