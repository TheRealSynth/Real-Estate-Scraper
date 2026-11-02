"""
Caching system for the Real Estate Scraper
"""
import os
import json
import hashlib
import time
import sqlite3
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import asdict

class CacheManager:
    """Manage caching for scraped data and API responses"""
    
    def __init__(self, cache_dir: str = "cache", cache_expiry_hours: int = 24):
        self.cache_dir = cache_dir
        self.cache_expiry = timedelta(hours=cache_expiry_hours)
        self.logger = logging.getLogger(__name__)
        
        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)
        
        # Initialize cache database
        self.db_path = os.path.join(cache_dir, "cache.db")
        self._init_cache_db()
    
    def _init_cache_db(self):
        """Initialize cache database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    data TEXT,
                    timestamp TEXT,
                    expiry_time TEXT,
                    content_type TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Error initializing cache database: {e}")
    
    def _generate_cache_key(self, url: str, params: Dict[str, Any] = None) -> str:
        """Generate a unique cache key for a URL and parameters"""
        # Combine URL and sorted parameters
        cache_input = url
        if params:
            sorted_params = sorted(params.items())
            cache_input += str(sorted_params)
        
        # Generate MD5 hash
        return hashlib.md5(cache_input.encode()).hexdigest()
    
    def get_cached_data(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached data if it exists and hasn't expired"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT data, expiry_time FROM cache_entries WHERE key = ?",
                (key,)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result:
                data_json, expiry_str = result
                expiry_time = datetime.fromisoformat(expiry_str)
                
                # Check if cache has expired
                if datetime.now() < expiry_time:
                    self.logger.debug(f"Cache hit for key: {key}")
                    return json.loads(data_json)
                else:
                    self.logger.debug(f"Cache expired for key: {key}")
                    self._remove_cache_entry(key)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error retrieving cached data: {e}")
            return None
    
    def store_cached_data(self, key: str, data: Any, content_type: str = "json") -> bool:
        """Store data in cache"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate expiry time
            expiry_time = datetime.now() + self.cache_expiry
            
            # Serialize data
            if content_type == "json":
                data_json = json.dumps(data, default=str)
            else:
                data_json = str(data)
            
            cursor.execute('''
                INSERT OR REPLACE INTO cache_entries 
                (key, data, timestamp, expiry_time, content_type)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                key,
                data_json,
                datetime.now().isoformat(),
                expiry_time.isoformat(),
                content_type
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.debug(f"Cached data for key: {key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing cached data: {e}")
            return False
    
    def _remove_cache_entry(self, key: str):
        """Remove a cache entry"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Error removing cache entry: {e}")
    
    def get_cached_page(self, url: str, params: Dict[str, Any] = None) -> Optional[str]:
        """Get cached HTML page content"""
        key = self._generate_cache_key(url, params)
        cached_data = self.get_cached_data(key)
        
        if cached_data and isinstance(cached_data, dict):
            return cached_data.get('content')
        
        return None
    
    def store_cached_page(self, url: str, content: str, params: Dict[str, Any] = None) -> bool:
        """Store HTML page content in cache"""
        key = self._generate_cache_key(url, params)
        data = {
            'url': url,
            'content': content,
            'params': params,
            'cached_at': datetime.now().isoformat()
        }
        
        return self.store_cached_data(key, data, "json")
    
    def get_cached_properties(self, search_criteria: Any) -> Optional[List[Dict[str, Any]]]:
        """Get cached property search results"""
        # Convert search criteria to dict for caching
        if hasattr(search_criteria, '__dict__'):
            criteria_dict = search_criteria.__dict__
        else:
            criteria_dict = search_criteria
        
        key = self._generate_cache_key("property_search", criteria_dict)
        cached_data = self.get_cached_data(key)
        
        if cached_data and isinstance(cached_data, dict):
            return cached_data.get('properties', [])
        
        return None
    
    def store_cached_properties(self, search_criteria: Any, properties: List[Any]) -> bool:
        """Store property search results in cache"""
        # Convert search criteria to dict for caching
        if hasattr(search_criteria, '__dict__'):
            criteria_dict = search_criteria.__dict__
        else:
            criteria_dict = search_criteria
        
        # Convert properties to dicts
        properties_list = []
        for prop in properties:
            if hasattr(prop, 'to_dict'):
                properties_list.append(prop.to_dict())
            elif hasattr(prop, '__dict__'):
                properties_list.append(prop.__dict__)
            else:
                properties_list.append(prop)
        
        key = self._generate_cache_key("property_search", criteria_dict)
        data = {
            'search_criteria': criteria_dict,
            'properties': properties_list,
            'cached_at': datetime.now().isoformat(),
            'property_count': len(properties_list)
        }
        
        return self.store_cached_data(key, data, "json")
    
    def clear_cache(self, older_than_hours: Optional[int] = None) -> int:
        """Clear cache entries, optionally only those older than specified hours"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if older_than_hours:
                cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
                cursor.execute(
                    "DELETE FROM cache_entries WHERE timestamp < ?",
                    (cutoff_time.isoformat(),)
                )
            else:
                cursor.execute("DELETE FROM cache_entries")
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            self.logger.info(f"Cleared {deleted_count} cache entries")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total entries
            cursor.execute("SELECT COUNT(*) FROM cache_entries")
            total_entries = cursor.fetchone()[0]
            
            # Expired entries
            cursor.execute(
                "SELECT COUNT(*) FROM cache_entries WHERE expiry_time < ?",
                (datetime.now().isoformat(),)
            )
            expired_entries = cursor.fetchone()[0]
            
            # Content type distribution
            cursor.execute("SELECT content_type, COUNT(*) FROM cache_entries GROUP BY content_type")
            content_types = dict(cursor.fetchall())
            
            # Cache size (approximate)
            cursor.execute("SELECT SUM(LENGTH(data)) FROM cache_entries")
            total_size = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'total_entries': total_entries,
                'expired_entries': expired_entries,
                'active_entries': total_entries - expired_entries,
                'content_types': content_types,
                'total_size_bytes': total_size,
                'cache_dir': self.cache_dir,
                'expiry_hours': self.cache_expiry.total_seconds() / 3600
            }
            
        except Exception as e:
            self.logger.error(f"Error getting cache stats: {e}")
            return {}

class RateLimiter:
    """Rate limiting to prevent overwhelming target websites"""
    
    def __init__(self, max_requests_per_minute: int = 30):
        self.max_requests = max_requests_per_minute
        self.requests = []
        self.logger = logging.getLogger(__name__)
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = time.time()
        
        # Remove requests older than 1 minute
        self.requests = [req_time for req_time in self.requests if now - req_time < 60]
        
        # Check if we need to wait
        if len(self.requests) >= self.max_requests:
            # Calculate wait time until oldest request is > 1 minute old
            oldest_request = min(self.requests)
            wait_time = 60 - (now - oldest_request) + 1  # Add 1 second buffer
            
            if wait_time > 0:
                self.logger.info(f"Rate limit reached, waiting {wait_time:.1f} seconds")
                time.sleep(wait_time)
                
                # Clean up after waiting
                now = time.time()
                self.requests = [req_time for req_time in self.requests if now - req_time < 60]
        
        # Record this request
        self.requests.append(now)

class PerformanceMonitor:
    """Monitor scraping performance and provide optimization suggestions"""
    
    def __init__(self):
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_time': 0,
            'properties_scraped': 0,
            'start_time': time.time()
        }
        self.request_times = []
        self.logger = logging.getLogger(__name__)
    
    def record_request(self, success: bool, response_time: float):
        """Record a request and its performance"""
        self.metrics['total_requests'] += 1
        
        if success:
            self.metrics['successful_requests'] += 1
        else:
            self.metrics['failed_requests'] += 1
        
        self.request_times.append(response_time)
        self.metrics['total_time'] += response_time
    
    def record_cache_hit(self):
        """Record a cache hit"""
        self.metrics['cache_hits'] += 1
    
    def record_cache_miss(self):
        """Record a cache miss"""
        self.metrics['cache_misses'] += 1
    
    def record_properties_scraped(self, count: int):
        """Record number of properties scraped"""
        self.metrics['properties_scraped'] += count
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report"""
        total_time = time.time() - self.metrics['start_time']
        
        # Calculate averages
        avg_request_time = (
            self.metrics['total_time'] / max(self.metrics['total_requests'], 1)
        )
        
        success_rate = (
            self.metrics['successful_requests'] / max(self.metrics['total_requests'], 1) * 100
        )
        
        cache_hit_rate = (
            self.metrics['cache_hits'] / max(self.metrics['cache_hits'] + self.metrics['cache_misses'], 1) * 100
        )
        
        properties_per_minute = (
            self.metrics['properties_scraped'] / max(total_time / 60, 1)
        )
        
        return {
            'session_duration': total_time,
            'total_requests': self.metrics['total_requests'],
            'success_rate': success_rate,
            'avg_request_time': avg_request_time,
            'cache_hit_rate': cache_hit_rate,
            'properties_scraped': self.metrics['properties_scraped'],
            'properties_per_minute': properties_per_minute,
            'total_cache_hits': self.metrics['cache_hits'],
            'total_cache_misses': self.metrics['cache_misses']
        }
    
    def get_optimization_suggestions(self) -> List[str]:
        """Get suggestions for performance optimization"""
        suggestions = []
        report = self.get_performance_report()
        
        if report['success_rate'] < 80:
            suggestions.append("Low success rate - consider reducing request frequency or using different scrapers")
        
        if report['avg_request_time'] > 5:
            suggestions.append("High average request time - consider using faster selectors or caching")
        
        if report['cache_hit_rate'] < 20 and self.metrics['cache_hits'] + self.metrics['cache_misses'] > 10:
            suggestions.append("Low cache hit rate - consider increasing cache expiry time")
        
        if report['properties_per_minute'] < 5:
            suggestions.append("Low scraping rate - consider parallel processing or optimizing selectors")
        
        if len(self.request_times) > 0:
            import statistics
            if statistics.stdev(self.request_times) > 3:
                suggestions.append("High request time variance - some pages may be problematic")
        
        return suggestions