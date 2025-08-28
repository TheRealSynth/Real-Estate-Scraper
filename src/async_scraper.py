"""
Asynchronous Real Estate Scraper for improved performance
"""
import asyncio
import aiohttp
import time
import logging
from typing import List, Optional, Dict, Any, Coroutine
from datetime import datetime
import json

from .models import Property, SearchCriteria
from .validators import PropertyValidator

class AsyncBaseScraper:
    """Asynchronous base scraper class"""
    
    def __init__(self, max_concurrent: int = 10, request_delay: float = 1.0):
        self.max_concurrent = max_concurrent
        self.request_delay = request_delay
        self.session = None
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.logger = logging.getLogger(__name__)
        self.validator = PropertyValidator()
        
        # User agent rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]
        self.current_user_agent = 0
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close_session()
    
    async def start_session(self):
        """Start aiohttp session"""
        timeout = aiohttp.ClientTimeout(total=30)
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=20)
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
        )
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
    
    def get_user_agent(self) -> str:
        """Get next user agent for rotation"""
        ua = self.user_agents[self.current_user_agent]
        self.current_user_agent = (self.current_user_agent + 1) % len(self.user_agents)
        return ua
    
    async def fetch_page(self, url: str, retries: int = 3) -> Optional[str]:
        """Fetch a single page asynchronously"""
        async with self.semaphore:  # Limit concurrent requests
            for attempt in range(retries):
                try:
                    # Add delay between requests
                    if attempt > 0:
                        await asyncio.sleep(self.request_delay * (attempt + 1))
                    else:
                        await asyncio.sleep(self.request_delay)
                    
                    headers = {'User-Agent': self.get_user_agent()}
                    
                    async with self.session.get(url, headers=headers) as response:
                        if response.status == 200:
                            content = await response.text()
                            self.logger.debug(f"Successfully fetched: {url}")
                            return content
                        elif response.status == 429:  # Rate limited
                            self.logger.warning(f"Rate limited on {url}, waiting...")
                            await asyncio.sleep(self.request_delay * 5)
                        else:
                            self.logger.warning(f"HTTP {response.status} for {url}")
                
                except asyncio.TimeoutError:
                    self.logger.warning(f"Timeout for {url} (attempt {attempt + 1})")
                except Exception as e:
                    self.logger.error(f"Error fetching {url}: {str(e)}")
            
            self.logger.error(f"Failed to fetch {url} after {retries} attempts")
            return None
    
    async def fetch_multiple_pages(self, urls: List[str]) -> List[Optional[str]]:
        """Fetch multiple pages concurrently"""
        self.logger.info(f"Fetching {len(urls)} pages concurrently...")
        
        # Create tasks for all URLs
        tasks = [self.fetch_page(url) for url in urls]
        
        # Execute all tasks concurrently
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # Process results
        pages = []
        successful = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Exception for {urls[i]}: {result}")
                pages.append(None)
            elif result is not None:
                pages.append(result)
                successful += 1
            else:
                pages.append(None)
        
        self.logger.info(f"Fetched {successful}/{len(urls)} pages in {end_time - start_time:.2f}s")
        return pages

class AsyncPropertyScraper(AsyncBaseScraper):
    """Async scraper specifically for property data"""
    
    def __init__(self, max_concurrent: int = 5, request_delay: float = 2.0):
        super().__init__(max_concurrent, request_delay)
        self.scraped_properties = []
        self.failed_urls = []
    
    async def scrape_property_urls(self, urls: List[str]) -> List[Property]:
        """Scrape multiple property URLs concurrently"""
        self.logger.info(f"Starting async scraping of {len(urls)} properties...")
        
        # Fetch all pages
        pages = await self.fetch_multiple_pages(urls)
        
        # Parse properties from pages
        properties = []
        for i, (url, page_content) in enumerate(zip(urls, pages)):
            if page_content:
                try:
                    property_data = await self.parse_property_page(url, page_content)
                    if property_data:
                        # Validate property data
                        is_valid, errors = self.validator.validate_property(property_data.to_dict())
                        if is_valid:
                            properties.append(property_data)
                        else:
                            self.logger.warning(f"Invalid property data for {url}: {errors}")
                    
                except Exception as e:
                    self.logger.error(f"Error parsing property {url}: {str(e)}")
                    self.failed_urls.append(url)
            else:
                self.failed_urls.append(url)
        
        self.scraped_properties.extend(properties)
        self.logger.info(f"Successfully scraped {len(properties)} valid properties")
        return properties
    
    async def parse_property_page(self, url: str, content: str) -> Optional[Property]:
        """Parse property data from page content - to be implemented by subclasses"""
        # This would contain site-specific parsing logic
        # For now, return a mock property for demonstration
        try:
            # Extract basic info from URL and content length as a demo
            property_id = url.split('/')[-1] if '/' in url else 'unknown'
            
            # Mock property data based on content analysis
            mock_property = Property(
                id=f"async_{property_id}",
                title=f"Async Scraped Property {property_id}",
                price=500000 + (len(content) % 500000),  # Mock price based on content
                address=f"123 Async Street, Demo City, State",
                bedrooms=2 + (len(content) % 4),
                bathrooms=1.5 + (len(content) % 3),
                square_feet=1000 + (len(content) % 2000),
                property_type="House",
                source_url=url,
                source_website="AsyncDemo",
                scraped_at=datetime.now()
            )
            
            return mock_property
            
        except Exception as e:
            self.logger.error(f"Error parsing property page: {str(e)}")
            return None
    
    async def scrape_search_results(self, search_criteria: SearchCriteria, max_properties: int = 100) -> List[Property]:
        """Scrape search results pages and extract property URLs"""
        # Generate mock URLs for demonstration
        base_url = "https://example-realestate.com/property/"
        property_urls = [f"{base_url}{i}" for i in range(1, min(max_properties + 1, 51))]
        
        self.logger.info(f"Generated {len(property_urls)} property URLs for async scraping")
        
        # Scrape all properties asynchronously
        properties = await self.scrape_property_urls(property_urls)
        
        # Apply search criteria filtering
        filtered_properties = self.filter_properties(properties, search_criteria)
        
        return filtered_properties
    
    def filter_properties(self, properties: List[Property], criteria: SearchCriteria) -> List[Property]:
        """Filter properties based on search criteria"""
        filtered = []
        
        for prop in properties:
            # Price filtering
            if criteria.min_price and prop.price and prop.price < criteria.min_price:
                continue
            if criteria.max_price and prop.price and prop.price > criteria.max_price:
                continue
            
            # Bedroom filtering
            if criteria.min_bedrooms and prop.bedrooms and prop.bedrooms < criteria.min_bedrooms:
                continue
            if criteria.max_bedrooms and prop.bedrooms and prop.bedrooms > criteria.max_bedrooms:
                continue
            
            # Property type filtering
            if criteria.property_types and prop.property_type:
                if prop.property_type.lower() not in [pt.lower() for pt in criteria.property_types]:
                    continue
            
            filtered.append(prop)
        
        self.logger.info(f"Filtered {len(filtered)} properties from {len(properties)} total")
        return filtered
    
    def get_scraping_stats(self) -> Dict[str, Any]:
        """Get statistics about the scraping session"""
        return {
            'total_properties_scraped': len(self.scraped_properties),
            'failed_urls': len(self.failed_urls),
            'success_rate': len(self.scraped_properties) / max(len(self.scraped_properties) + len(self.failed_urls), 1) * 100,
            'max_concurrent': self.max_concurrent,
            'request_delay': self.request_delay
        }

class AsyncScrapingManager:
    """Manager for coordinating multiple async scraping tasks"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.active_scrapers = {}
        self.completed_jobs = []
    
    async def run_scraping_job(self, job_id: str, search_criteria: SearchCriteria, 
                              max_properties: int = 100, max_concurrent: int = 5) -> Dict[str, Any]:
        """Run a complete scraping job asynchronously"""
        self.logger.info(f"Starting async scraping job {job_id}")
        start_time = time.time()
        
        try:
            async with AsyncPropertyScraper(max_concurrent=max_concurrent) as scraper:
                self.active_scrapers[job_id] = scraper
                
                # Scrape properties
                properties = await scraper.scrape_search_results(search_criteria, max_properties)
                
                # Get stats
                stats = scraper.get_scraping_stats()
                
                end_time = time.time()
                
                job_result = {
                    'job_id': job_id,
                    'status': 'completed',
                    'properties': [prop.to_dict() for prop in properties],
                    'property_count': len(properties),
                    'duration': end_time - start_time,
                    'search_criteria': search_criteria.__dict__,
                    'stats': stats,
                    'completed_at': datetime.now().isoformat()
                }
                
                self.completed_jobs.append(job_result)
                
                if job_id in self.active_scrapers:
                    del self.active_scrapers[job_id]
                
                self.logger.info(f"Completed job {job_id}: {len(properties)} properties in {end_time - start_time:.2f}s")
                return job_result
                
        except Exception as e:
            self.logger.error(f"Error in scraping job {job_id}: {str(e)}")
            
            error_result = {
                'job_id': job_id,
                'status': 'failed',
                'error': str(e),
                'duration': time.time() - start_time,
                'completed_at': datetime.now().isoformat()
            }
            
            self.completed_jobs.append(error_result)
            
            if job_id in self.active_scrapers:
                del self.active_scrapers[job_id]
            
            return error_result
    
    async def run_multiple_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run multiple scraping jobs concurrently"""
        self.logger.info(f"Starting {len(jobs)} concurrent scraping jobs")
        
        # Create tasks for all jobs
        tasks = []
        for job in jobs:
            task = self.run_scraping_job(
                job['job_id'],
                job['search_criteria'],
                job.get('max_properties', 100),
                job.get('max_concurrent', 5)
            )
            tasks.append(task)
        
        # Run all jobs concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        job_results = []
        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"Job failed with exception: {result}")
                job_results.append({
                    'status': 'failed',
                    'error': str(result)
                })
            else:
                job_results.append(result)
        
        return job_results
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of a specific job"""
        # Check active jobs
        if job_id in self.active_scrapers:
            return {
                'job_id': job_id,
                'status': 'running',
                'properties_scraped': len(self.active_scrapers[job_id].scraped_properties)
            }
        
        # Check completed jobs
        for job in self.completed_jobs:
            if job.get('job_id') == job_id:
                return job
        
        return {'job_id': job_id, 'status': 'not_found'}
    
    def get_all_jobs_status(self) -> Dict[str, Any]:
        """Get status of all jobs"""
        return {
            'active_jobs': len(self.active_scrapers),
            'completed_jobs': len(self.completed_jobs),
            'active_job_ids': list(self.active_scrapers.keys()),
            'recent_completed': self.completed_jobs[-5:] if self.completed_jobs else []
        }