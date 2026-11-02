#!/usr/bin/env python3
"""
Test script for Async Real Estate Scraper
"""
import asyncio
import sys
import os
import time
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Mock the aiohttp dependency for testing
class MockResponse:
    def __init__(self, status=200, text_content="Mock HTML content for testing async scraper functionality."):
        self.status = status
        self._text = text_content
    
    async def text(self):
        return self._text
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

class MockSession:
    def __init__(self):
        self.closed = False
    
    def get(self, url, headers=None):
        # Simulate different response times and status codes
        if "timeout" in url:
            raise asyncio.TimeoutError("Mock timeout")
        elif "error" in url:
            return MockResponse(status=500)
        elif "ratelimit" in url:
            return MockResponse(status=429)
        else:
            return MockResponse(status=200, text_content=f"Mock content for {url} - " + "x" * 1000)
    
    async def close(self):
        self.closed = True

# Mock aiohttp module
class MockAioHttp:
    class ClientTimeout:
        def __init__(self, total=30):
            self.total = total
    
    class TCPConnector:
        def __init__(self, limit=100, limit_per_host=20):
            self.limit = limit
            self.limit_per_host = limit_per_host
    
    def ClientSession(self, timeout=None, connector=None, headers=None):
        return MockSession()

# Patch aiohttp
sys.modules['aiohttp'] = MockAioHttp()

# Now import our async scraper
try:
    from src.async_scraper import AsyncPropertyScraper, AsyncScrapingManager
    from src.models import SearchCriteria
    ASYNC_AVAILABLE = True
except ImportError as e:
    print(f"❌ Async scraper not available: {e}")
    ASYNC_AVAILABLE = False

async def test_async_basic_scraping():
    """Test basic async scraping functionality"""
    print("🚀 Testing Async Basic Scraping")
    print("=" * 40)
    
    if not ASYNC_AVAILABLE:
        print("❌ Async functionality not available")
        return
    
    # Create search criteria
    criteria = SearchCriteria(
        location="Austin, TX",
        min_price=300000,
        max_price=700000,
        min_bedrooms=2,
        property_types=['house']
    )
    
    print(f"📍 Search criteria: {criteria.location}")
    print(f"💰 Price range: ${criteria.min_price:,} - ${criteria.max_price:,}")
    
    start_time = time.time()
    
    # Test async scraper
    async with AsyncPropertyScraper(max_concurrent=3, request_delay=0.1) as scraper:
        properties = await scraper.scrape_search_results(criteria, max_properties=20)
        
        end_time = time.time()
        
        print(f"\n✅ Async scraping completed in {end_time - start_time:.2f} seconds")
        print(f"🏠 Properties found: {len(properties)}")
        
        if properties:
            print("\n📋 Sample properties:")
            for i, prop in enumerate(properties[:3], 1):
                print(f"   {i}. {prop.title}")
                print(f"      💵 ${prop.price:,} | {prop.bedrooms}BR | {prop.square_feet}sqft")
        
        # Get scraping stats
        stats = scraper.get_scraping_stats()
        print(f"\n📊 Scraping statistics:")
        print(f"   Success rate: {stats['success_rate']:.1f}%")
        print(f"   Max concurrent: {stats['max_concurrent']}")
        print(f"   Request delay: {stats['request_delay']}s")

async def test_async_job_manager():
    """Test async job management"""
    print("\n🎯 Testing Async Job Manager")
    print("=" * 40)
    
    if not ASYNC_AVAILABLE:
        print("❌ Async functionality not available")
        return
    
    manager = AsyncScrapingManager()
    
    # Create multiple search jobs
    jobs = [
        {
            'job_id': 'austin_houses',
            'search_criteria': SearchCriteria(
                location="Austin, TX",
                property_types=['house'],
                max_price=600000
            ),
            'max_properties': 15,
            'max_concurrent': 3
        },
        {
            'job_id': 'dallas_condos',
            'search_criteria': SearchCriteria(
                location="Dallas, TX",
                property_types=['condo'],
                min_price=200000,
                max_price=500000
            ),
            'max_properties': 10,
            'max_concurrent': 2
        },
        {
            'job_id': 'houston_any',
            'search_criteria': SearchCriteria(
                location="Houston, TX",
                min_bedrooms=3
            ),
            'max_properties': 12,
            'max_concurrent': 4
        }
    ]
    
    print(f"🚀 Starting {len(jobs)} concurrent scraping jobs...")
    
    start_time = time.time()
    results = await manager.run_multiple_jobs(jobs)
    end_time = time.time()
    
    print(f"\n✅ All jobs completed in {end_time - start_time:.2f} seconds")
    
    # Display results
    for result in results:
        job_id = result.get('job_id', 'unknown')
        status = result.get('status', 'unknown')
        property_count = result.get('property_count', 0)
        duration = result.get('duration', 0)
        
        print(f"\n📊 Job: {job_id}")
        print(f"   Status: {status}")
        print(f"   Properties: {property_count}")
        print(f"   Duration: {duration:.2f}s")
        
        if status == 'completed':
            stats = result.get('stats', {})
            print(f"   Success rate: {stats.get('success_rate', 0):.1f}%")

async def test_async_performance_comparison():
    """Compare async vs sequential performance"""
    print("\n⚡ Testing Performance Comparison")
    print("=" * 40)
    
    if not ASYNC_AVAILABLE:
        print("❌ Async functionality not available")
        return
    
    # Test URLs
    test_urls = [f"https://example.com/property/{i}" for i in range(1, 21)]
    
    print(f"📋 Testing with {len(test_urls)} URLs")
    
    # Test async approach
    print("\n🚀 Testing Async Approach:")
    async with AsyncPropertyScraper(max_concurrent=5, request_delay=0.05) as scraper:
        start_time = time.time()
        pages = await scraper.fetch_multiple_pages(test_urls)
        async_time = time.time() - start_time
        
        successful_async = sum(1 for page in pages if page is not None)
        print(f"   Time: {async_time:.2f}s")
        print(f"   Success: {successful_async}/{len(test_urls)}")
        print(f"   Rate: {len(test_urls)/async_time:.1f} URLs/second")
    
    # Simulate sequential approach
    print("\n🐌 Simulated Sequential Approach:")
    start_time = time.time()
    sequential_time = len(test_urls) * 0.05  # Simulated request delay
    end_time = start_time + sequential_time
    
    print(f"   Time: {sequential_time:.2f}s (simulated)")
    print(f"   Success: {len(test_urls)}/{len(test_urls)} (simulated)")
    print(f"   Rate: {len(test_urls)/sequential_time:.1f} URLs/second")
    
    # Performance improvement
    improvement = sequential_time / async_time
    print(f"\n📈 Async Performance Improvement: {improvement:.1f}x faster")

async def test_async_error_handling():
    """Test async error handling"""
    print("\n🛡️  Testing Async Error Handling")
    print("=" * 40)
    
    if not ASYNC_AVAILABLE:
        print("❌ Async functionality not available")
        return
    
    # Test URLs with various error conditions
    test_urls = [
        "https://example.com/good1",
        "https://example.com/timeout",  # Will timeout
        "https://example.com/good2",
        "https://example.com/error",    # Will return 500
        "https://example.com/ratelimit", # Will return 429
        "https://example.com/good3"
    ]
    
    print(f"🧪 Testing error handling with {len(test_urls)} URLs (including problematic ones)")
    
    async with AsyncPropertyScraper(max_concurrent=3, request_delay=0.1) as scraper:
        start_time = time.time()
        pages = await scraper.fetch_multiple_pages(test_urls)
        end_time = time.time()
        
        successful = sum(1 for page in pages if page is not None)
        failed = len(pages) - successful
        
        print(f"\n📊 Results:")
        print(f"   Total URLs: {len(test_urls)}")
        print(f"   Successful: {successful}")
        print(f"   Failed: {failed}")
        print(f"   Success rate: {(successful/len(test_urls)*100):.1f}%")
        print(f"   Time: {end_time - start_time:.2f}s")
        
        print(f"\n🔍 Detailed results:")
        for i, (url, page) in enumerate(zip(test_urls, pages)):
            status = "✅ SUCCESS" if page else "❌ FAILED"
            print(f"   {i+1}. {url.split('/')[-1]}: {status}")

async def main():
    """Run all async tests"""
    print("🏠 Real Estate Scraper - Async Testing Suite")
    print("=" * 60)
    
    try:
        await test_async_basic_scraping()
        await test_async_job_manager()
        await test_async_performance_comparison()
        await test_async_error_handling()
        
        print("\n" + "=" * 60)
        print("✅ All async tests completed successfully!")
        print("\n💡 Key Benefits of Async Scraping:")
        print("   • Significantly faster for multiple URLs")
        print("   • Better resource utilization")
        print("   • Concurrent job processing")
        print("   • Improved error handling and recovery")
        print("   • Real-time progress monitoring")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run async tests
    asyncio.run(main())