#!/usr/bin/env python3
"""
Job Scheduler for Real Estate Scraper
Automated scheduling of scraping jobs with configurable intervals
"""
import sys
import os
import time
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Mock schedule module for testing
class MockSchedule:
    def __init__(self):
        self.jobs = []
    
    def every(self, interval=None):
        return MockJob(self, interval)
    
    def run_pending(self):
        current_time = datetime.now()
        for job in self.jobs:
            if job.should_run(current_time):
                print(f"🕐 Running scheduled job: {job.name}")
                try:
                    job.run()
                    job.last_run = current_time
                    print(f"✅ Job completed: {job.name}")
                except Exception as e:
                    print(f"❌ Job failed: {job.name} - {e}")

class MockJob:
    def __init__(self, scheduler, interval):
        self.scheduler = scheduler
        self.interval = interval
        self.job_func = None
        self.name = "unknown"
        self.last_run = None
        self.unit = None
    
    def minutes(self):
        self.unit = 'minutes'
        return self
    
    def hours(self):
        self.unit = 'hours'
        return self
    
    def days(self):
        self.unit = 'days'
        return self
    
    def at(self, time_str):
        self.at_time = time_str
        return self
    
    def do(self, func, *args, **kwargs):
        self.job_func = lambda: func(*args, **kwargs)
        self.name = func.__name__
        self.scheduler.jobs.append(self)
        return self
    
    def should_run(self, current_time):
        if not self.last_run:
            return True
        
        if self.unit == 'minutes':
            return current_time >= self.last_run + timedelta(minutes=self.interval)
        elif self.unit == 'hours':
            return current_time >= self.last_run + timedelta(hours=self.interval)
        elif self.unit == 'days':
            return current_time >= self.last_run + timedelta(days=self.interval)
        
        return False
    
    def run(self):
        if self.job_func:
            self.job_func()

# Try to import real schedule, fallback to mock
try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    schedule = MockSchedule()
    SCHEDULE_AVAILABLE = False

try:
    from src.models import SearchCriteria
    from src.data_manager import DataManager
    from src.async_scraper import AsyncScrapingManager
    SCRAPER_AVAILABLE = True
except ImportError:
    SCRAPER_AVAILABLE = False

class JobScheduler:
    """Main job scheduler class"""
    
    def __init__(self, config_file: str = "config/scheduled_jobs.json"):
        self.config_file = config_file
        self.logger = logging.getLogger(__name__)
        self.jobs_config = self.load_jobs_config()
        self.data_manager = DataManager() if SCRAPER_AVAILABLE else None
        self.scraping_manager = AsyncScrapingManager() if SCRAPER_AVAILABLE else None
        self.job_history = []
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/scheduler.log'),
                logging.StreamHandler()
            ]
        )
    
    def load_jobs_config(self) -> List[Dict[str, Any]]:
        """Load job configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            else:
                # Create default configuration
                default_config = self.create_default_config()
                self.save_jobs_config(default_config)
                return default_config
        except Exception as e:
            self.logger.error(f"Error loading job config: {e}")
            return self.create_default_config()
    
    def save_jobs_config(self, config: List[Dict[str, Any]]):
        """Save job configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving job config: {e}")
    
    def create_default_config(self) -> List[Dict[str, Any]]:
        """Create default job configuration"""
        return [
            {
                "name": "daily_austin_houses",
                "description": "Daily scraping of Austin houses under $800k",
                "enabled": True,
                "schedule": {
                    "type": "daily",
                    "time": "09:00"
                },
                "search_criteria": {
                    "location": "Austin, TX",
                    "max_price": 800000,
                    "property_types": ["house"],
                    "max_pages": 10
                },
                "options": {
                    "max_properties": 100,
                    "max_concurrent": 5,
                    "export_format": "database"
                }
            },
            {
                "name": "weekly_market_analysis",
                "description": "Weekly comprehensive market analysis",
                "enabled": True,
                "schedule": {
                    "type": "weekly",
                    "day": "monday",
                    "time": "06:00"
                },
                "search_criteria": {
                    "location": "Dallas, TX",
                    "min_price": 200000,
                    "max_price": 1000000,
                    "max_pages": 20
                },
                "options": {
                    "max_properties": 200,
                    "max_concurrent": 3,
                    "export_format": "csv"
                }
            },
            {
                "name": "hourly_luxury_properties",
                "description": "Monitor luxury properties every 2 hours",
                "enabled": False,
                "schedule": {
                    "type": "interval",
                    "hours": 2
                },
                "search_criteria": {
                    "location": "San Francisco, CA",
                    "min_price": 2000000,
                    "property_types": ["house", "condo"],
                    "max_pages": 5
                },
                "options": {
                    "max_properties": 50,
                    "max_concurrent": 8,
                    "export_format": "json"
                }
            }
        ]
    
    def setup_scheduled_jobs(self):
        """Setup all scheduled jobs based on configuration"""
        self.logger.info("Setting up scheduled jobs...")
        
        for job_config in self.jobs_config:
            if not job_config.get('enabled', True):
                self.logger.info(f"Skipping disabled job: {job_config['name']}")
                continue
            
            try:
                self.schedule_job(job_config)
                self.logger.info(f"Scheduled job: {job_config['name']}")
            except Exception as e:
                self.logger.error(f"Failed to schedule job {job_config['name']}: {e}")
        
        self.logger.info(f"Setup complete. {len(schedule.jobs)} jobs scheduled.")
    
    def schedule_job(self, job_config: Dict[str, Any]):
        """Schedule a single job based on its configuration"""
        schedule_config = job_config['schedule']
        job_name = job_config['name']
        
        if schedule_config['type'] == 'daily':
            schedule.every().day.at(schedule_config['time']).do(
                self.run_scraping_job, job_config
            )
        
        elif schedule_config['type'] == 'weekly':
            day = schedule_config.get('day', 'monday').lower()
            time_str = schedule_config.get('time', '09:00')
            
            if day == 'monday':
                schedule.every().monday.at(time_str).do(self.run_scraping_job, job_config)
            elif day == 'tuesday':
                schedule.every().tuesday.at(time_str).do(self.run_scraping_job, job_config)
            elif day == 'wednesday':
                schedule.every().wednesday.at(time_str).do(self.run_scraping_job, job_config)
            elif day == 'thursday':
                schedule.every().thursday.at(time_str).do(self.run_scraping_job, job_config)
            elif day == 'friday':
                schedule.every().friday.at(time_str).do(self.run_scraping_job, job_config)
            elif day == 'saturday':
                schedule.every().saturday.at(time_str).do(self.run_scraping_job, job_config)
            elif day == 'sunday':
                schedule.every().sunday.at(time_str).do(self.run_scraping_job, job_config)
        
        elif schedule_config['type'] == 'interval':
            if 'minutes' in schedule_config:
                schedule.every(schedule_config['minutes']).minutes.do(
                    self.run_scraping_job, job_config
                )
            elif 'hours' in schedule_config:
                schedule.every(schedule_config['hours']).hours.do(
                    self.run_scraping_job, job_config
                )
            elif 'days' in schedule_config:
                schedule.every(schedule_config['days']).days.do(
                    self.run_scraping_job, job_config
                )
    
    def run_scraping_job(self, job_config: Dict[str, Any]):
        """Execute a scraping job"""
        job_name = job_config['name']
        start_time = datetime.now()
        
        self.logger.info(f"Starting scheduled job: {job_name}")
        
        try:
            # Create search criteria
            criteria_data = job_config['search_criteria']
            
            if SCRAPER_AVAILABLE:
                criteria = SearchCriteria(
                    location=criteria_data['location'],
                    min_price=criteria_data.get('min_price'),
                    max_price=criteria_data.get('max_price'),
                    min_bedrooms=criteria_data.get('min_bedrooms'),
                    max_bedrooms=criteria_data.get('max_bedrooms'),
                    property_types=criteria_data.get('property_types', []),
                    max_pages=criteria_data.get('max_pages', 5)
                )
                
                # Get job options
                options = job_config.get('options', {})
                max_properties = options.get('max_properties', 100)
                max_concurrent = options.get('max_concurrent', 5)
                
                # Run the scraping job
                result = asyncio.run(self.scraping_manager.run_scraping_job(
                    job_id=f"{job_name}_{int(time.time())}",
                    search_criteria=criteria,
                    max_properties=max_properties,
                    max_concurrent=max_concurrent
                ))
                
                # Save results
                if result['status'] == 'completed':
                    properties_count = result['property_count']
                    duration = result['duration']
                    
                    self.logger.info(f"Job {job_name} completed: {properties_count} properties in {duration:.2f}s")
                    
                    # Record job execution
                    job_record = {
                        'job_name': job_name,
                        'start_time': start_time.isoformat(),
                        'end_time': datetime.now().isoformat(),
                        'status': 'completed',
                        'properties_count': properties_count,
                        'duration': duration
                    }
                    
                else:
                    self.logger.error(f"Job {job_name} failed: {result.get('error', 'Unknown error')}")
                    job_record = {
                        'job_name': job_name,
                        'start_time': start_time.isoformat(),
                        'end_time': datetime.now().isoformat(),
                        'status': 'failed',
                        'error': result.get('error', 'Unknown error')
                    }
            
            else:
                # Mock execution for testing
                self.logger.info(f"Mock execution of job: {job_name}")
                time.sleep(2)  # Simulate work
                
                job_record = {
                    'job_name': job_name,
                    'start_time': start_time.isoformat(),
                    'end_time': datetime.now().isoformat(),
                    'status': 'completed (mock)',
                    'properties_count': 25,
                    'duration': 2.0
                }
            
            # Add to job history
            self.job_history.append(job_record)
            
            # Keep only last 100 job records
            if len(self.job_history) > 100:
                self.job_history = self.job_history[-100:]
                
        except Exception as e:
            self.logger.error(f"Error running job {job_name}: {e}")
            
            job_record = {
                'job_name': job_name,
                'start_time': start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'status': 'error',
                'error': str(e)
            }
            self.job_history.append(job_record)
    
    def get_job_status(self) -> Dict[str, Any]:
        """Get current status of all scheduled jobs"""
        return {
            'total_jobs': len(self.jobs_config),
            'enabled_jobs': sum(1 for job in self.jobs_config if job.get('enabled', True)),
            'scheduled_jobs': len(schedule.jobs) if hasattr(schedule, 'jobs') else len(self.jobs_config),
            'job_history_count': len(self.job_history),
            'recent_executions': self.job_history[-10:] if self.job_history else [],
            'next_run': self.get_next_scheduled_time(),
            'scheduler_status': 'running',
            'schedule_available': SCHEDULE_AVAILABLE,
            'scraper_available': SCRAPER_AVAILABLE
        }
    
    def get_next_scheduled_time(self) -> Optional[str]:
        """Get the next scheduled job time"""
        try:
            if hasattr(schedule, 'jobs') and schedule.jobs:
                next_run = schedule.idle_seconds()
                if next_run is not None:
                    next_time = datetime.now() + timedelta(seconds=next_run)
                    return next_time.isoformat()
            return None
        except:
            return None
    
    def run_scheduler(self):
        """Main scheduler loop"""
        self.logger.info("🕐 Starting Real Estate Scraper Scheduler")
        
        # Setup jobs
        self.setup_scheduled_jobs()
        
        # Print job summary
        status = self.get_job_status()
        self.logger.info(f"📊 Scheduler Status:")
        self.logger.info(f"   Total jobs: {status['total_jobs']}")
        self.logger.info(f"   Enabled jobs: {status['enabled_jobs']}")
        self.logger.info(f"   Schedule library: {'Available' if status['schedule_available'] else 'Mock'}")
        self.logger.info(f"   Scraper: {'Available' if status['scraper_available'] else 'Mock'}")
        
        # Run scheduler loop
        self.logger.info("🔄 Scheduler running... Press Ctrl+C to stop")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
                
        except KeyboardInterrupt:
            self.logger.info("⏹️  Scheduler stopped by user")
        except Exception as e:
            self.logger.error(f"❌ Scheduler error: {e}")
        finally:
            self.logger.info("🛑 Scheduler shutdown complete")

def main():
    """Main entry point"""
    print("🕐 Real Estate Scraper - Job Scheduler")
    print("=" * 50)
    
    # Check for demo mode
    if len(sys.argv) > 1 and sys.argv[1] == '--demo':
        print("🎮 Running in demo mode...")
        demo_scheduler()
        return
    
    # Run actual scheduler
    scheduler = JobScheduler()
    scheduler.run_scheduler()

def demo_scheduler():
    """Run scheduler demonstration"""
    print("📋 Demonstrating job scheduling functionality...")
    
    scheduler = JobScheduler()
    
    # Show configuration
    print(f"\n📝 Loaded {len(scheduler.jobs_config)} job configurations:")
    for job in scheduler.jobs_config:
        status = "✅ Enabled" if job.get('enabled') else "❌ Disabled"
        schedule_type = job['schedule']['type']
        print(f"   • {job['name']} - {schedule_type} - {status}")
    
    # Setup jobs
    scheduler.setup_scheduled_jobs()
    
    # Show status
    status = scheduler.get_job_status()
    print(f"\n📊 Scheduler Status:")
    for key, value in status.items():
        if key != 'recent_executions':
            print(f"   {key}: {value}")
    
    # Simulate a few job runs
    print(f"\n🔄 Simulating job executions...")
    for i, job_config in enumerate(scheduler.jobs_config[:2]):
        if job_config.get('enabled'):
            print(f"\n🚀 Running job {i+1}: {job_config['name']}")
            scheduler.run_scraping_job(job_config)
    
    # Show final status
    final_status = scheduler.get_job_status()
    print(f"\n📈 Final Status:")
    print(f"   Recent executions: {final_status['job_history_count']}")
    
    if final_status['recent_executions']:
        print(f"\n📋 Recent Job History:")
        for execution in final_status['recent_executions']:
            status_emoji = "✅" if execution['status'] == 'completed' else "⚠️"
            print(f"   {status_emoji} {execution['job_name']} - {execution['status']}")

if __name__ == '__main__':
    main()