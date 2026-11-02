#!/usr/bin/env python3
"""
CLI utilities for Real Estate Scraper management and maintenance
"""
import os
import sys
import argparse
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def cache_command(args):
    """Handle cache-related commands"""
    try:
        from src.cache_manager import CacheManager
        
        cache_manager = CacheManager()
        
        if args.cache_action == 'stats':
            stats = cache_manager.get_cache_stats()
            print("📊 Cache Statistics:")
            print(f"   Total entries: {stats.get('total_entries', 0)}")
            print(f"   Active entries: {stats.get('active_entries', 0)}")
            print(f"   Expired entries: {stats.get('expired_entries', 0)}")
            print(f"   Cache size: {stats.get('total_size_bytes', 0):,} bytes")
            print(f"   Cache directory: {stats.get('cache_dir', 'N/A')}")
            print(f"   Expiry time: {stats.get('expiry_hours', 0)} hours")
            
            content_types = stats.get('content_types', {})
            if content_types:
                print("   Content types:")
                for content_type, count in content_types.items():
                    print(f"     {content_type}: {count}")
        
        elif args.cache_action == 'clear':
            if args.older_than:
                deleted = cache_manager.clear_cache(older_than_hours=args.older_than)
                print(f"🗑️  Cleared {deleted} cache entries older than {args.older_than} hours")
            else:
                deleted = cache_manager.clear_cache()
                print(f"🗑️  Cleared all {deleted} cache entries")
        
        elif args.cache_action == 'test':
            # Test cache functionality
            print("🧪 Testing cache functionality...")
            
            # Store test data
            test_key = "test_key"
            test_data = {"test": "data", "timestamp": datetime.now().isoformat()}
            
            success = cache_manager.store_cached_data(test_key, test_data)
            print(f"   Store test: {'✅ PASS' if success else '❌ FAIL'}")
            
            # Retrieve test data
            retrieved = cache_manager.get_cached_data(test_key)
            retrieve_success = retrieved is not None and retrieved.get('test') == 'data'
            print(f"   Retrieve test: {'✅ PASS' if retrieve_success else '❌ FAIL'}")
            
            # Clean up
            cache_manager._remove_cache_entry(test_key)
            print("   Cache test completed")
            
    except ImportError:
        print("❌ Cache functionality requires additional dependencies")
        print("💡 Install with: pip install -r requirements.txt")

def validate_command(args):
    """Handle data validation commands"""
    try:
        from src.validators import PropertyValidator, AddressParser
        
        validator = PropertyValidator()
        address_parser = AddressParser()
        
        if args.validate_action == 'test':
            print("🔍 Testing data validation...")
            
            # Test property validation
            test_properties = [
                {
                    'title': 'Valid Property',
                    'price': 500000,
                    'address': '123 Main Street, Austin, TX 78701',
                    'bedrooms': 3,
                    'bathrooms': 2.5,
                    'square_feet': 1800
                },
                {
                    'title': '',  # Invalid: empty title
                    'price': -100,  # Invalid: negative price
                    'address': 'Bad',  # Invalid: too short
                    'bedrooms': 0,  # Invalid: zero bedrooms
                }
            ]
            
            for i, prop in enumerate(test_properties, 1):
                is_valid, errors = validator.validate_property(prop)
                print(f"   Property {i}: {'✅ VALID' if is_valid else '❌ INVALID'}")
                if errors:
                    for error in errors:
                        print(f"     - {error}")
            
            # Test address parsing
            test_addresses = [
                "123 Main Street, Austin, TX 78701",
                "456 Oak Avenue, San Francisco, CA",
                "789 Pine St, Seattle, WA 98101-1234"
            ]
            
            print("\n📍 Address parsing test:")
            for address in test_addresses:
                parsed = address_parser.parse_address(address)
                print(f"   '{address}'")
                print(f"     Street: {parsed.get('street')}")
                print(f"     City: {parsed.get('city')}")
                print(f"     State: {parsed.get('state')}")
                print(f"     ZIP: {parsed.get('zip_code')}")
        
        elif args.validate_action == 'clean':
            if args.input_file:
                print(f"🧹 Cleaning data from {args.input_file}...")
                # This would implement file cleaning logic
                print("   File cleaning not implemented in test environment")
            else:
                print("❌ Input file required for cleaning")
                
    except ImportError:
        print("❌ Validation functionality requires additional dependencies")

def performance_command(args):
    """Handle performance monitoring commands"""
    try:
        from src.cache_manager import PerformanceMonitor
        
        monitor = PerformanceMonitor()
        
        if args.perf_action == 'test':
            print("⚡ Testing performance monitoring...")
            
            # Simulate some requests
            for i in range(5):
                success = i % 4 != 0  # 80% success rate
                response_time = 1.0 + (i * 0.5)  # Varying response times
                monitor.record_request(success, response_time)
                time.sleep(0.1)
            
            # Add some cache metrics
            monitor.record_cache_hit()
            monitor.record_cache_hit()
            monitor.record_cache_miss()
            
            monitor.record_properties_scraped(25)
            
            # Generate report
            report = monitor.get_performance_report()
            suggestions = monitor.get_optimization_suggestions()
            
            print("📊 Performance Report:")
            print(f"   Success rate: {report['success_rate']:.1f}%")
            print(f"   Average request time: {report['avg_request_time']:.2f}s")
            print(f"   Cache hit rate: {report['cache_hit_rate']:.1f}%")
            print(f"   Properties per minute: {report['properties_per_minute']:.1f}")
            
            if suggestions:
                print("\n💡 Optimization suggestions:")
                for suggestion in suggestions:
                    print(f"   - {suggestion}")
            
    except ImportError:
        print("❌ Performance monitoring requires additional dependencies")

def analyze_command(args):
    """Handle data analysis commands"""
    if args.analyze_action == 'demo':
        print("📈 Data Analysis Demo")
        print("=" * 30)
        
        # Mock property data for analysis
        properties = [
            {'price': 400000, 'bedrooms': 2, 'square_feet': 1200, 'property_type': 'condo', 'city': 'Austin'},
            {'price': 600000, 'bedrooms': 3, 'square_feet': 1800, 'property_type': 'house', 'city': 'Austin'},
            {'price': 550000, 'bedrooms': 3, 'square_feet': 1600, 'property_type': 'townhouse', 'city': 'Austin'},
            {'price': 750000, 'bedrooms': 4, 'square_feet': 2200, 'property_type': 'house', 'city': 'Austin'},
            {'price': 450000, 'bedrooms': 2, 'square_feet': 1100, 'property_type': 'condo', 'city': 'Austin'},
        ]
        
        # Basic statistics
        prices = [p['price'] for p in properties]
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        
        print(f"📊 Analysis of {len(properties)} properties:")
        print(f"💰 Average price: ${avg_price:,.2f}")
        print(f"📉 Min price: ${min_price:,}")
        print(f"📈 Max price: ${max_price:,}")
        
        # Price per square foot analysis
        price_per_sqft = []
        for prop in properties:
            if prop['square_feet']:
                ppsf = prop['price'] / prop['square_feet']
                price_per_sqft.append(ppsf)
        
        if price_per_sqft:
            avg_ppsf = sum(price_per_sqft) / len(price_per_sqft)
            print(f"🏠 Average price per sq ft: ${avg_ppsf:.2f}")
        
        # Property type analysis
        type_counts = {}
        type_avg_prices = {}
        
        for prop in properties:
            prop_type = prop['property_type']
            type_counts[prop_type] = type_counts.get(prop_type, 0) + 1
            
            if prop_type not in type_avg_prices:
                type_avg_prices[prop_type] = []
            type_avg_prices[prop_type].append(prop['price'])
        
        print("\n🏘️  Property type analysis:")
        for prop_type, count in type_counts.items():
            avg_price_type = sum(type_avg_prices[prop_type]) / len(type_avg_prices[prop_type])
            percentage = (count / len(properties)) * 100
            print(f"   {prop_type}: {count} properties ({percentage:.1f}%) - Avg: ${avg_price_type:,.0f}")
        
        # Bedroom analysis
        bedroom_counts = {}
        for prop in properties:
            bedrooms = prop['bedrooms']
            bedroom_counts[bedrooms] = bedroom_counts.get(bedrooms, 0) + 1
        
        print("\n🛏️  Bedroom distribution:")
        for bedrooms, count in sorted(bedroom_counts.items()):
            percentage = (count / len(properties)) * 100
            print(f"   {bedrooms} bedrooms: {count} properties ({percentage:.1f}%)")

def setup_command(args):
    """Handle setup and installation commands"""
    print("🔧 Real Estate Scraper Setup")
    print("=" * 30)
    
    if args.setup_action == 'check':
        print("📋 Checking system requirements...")
        
        # Check Python version
        python_version = sys.version_info
        print(f"   Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        if python_version >= (3, 8):
            print("   ✅ Python version OK")
        else:
            print("   ❌ Python 3.8+ required")
        
        # Check for required directories
        required_dirs = ['data', 'logs', 'cache']
        for directory in required_dirs:
            if os.path.exists(directory):
                print(f"   ✅ {directory}/ directory exists")
            else:
                print(f"   📁 Creating {directory}/ directory...")
                os.makedirs(directory, exist_ok=True)
        
        # Check for configuration files
        config_files = ['config/settings.py', 'requirements.txt']
        for config_file in config_files:
            if os.path.exists(config_file):
                print(f"   ✅ {config_file} exists")
            else:
                print(f"   ❌ {config_file} missing")
        
        # Try importing key modules
        modules_to_check = [
            ('requests', 'HTTP requests'),
            ('beautifulsoup4', 'HTML parsing'),
            ('selenium', 'Browser automation'),
            ('pandas', 'Data analysis'),
        ]
        
        print("\n📦 Checking dependencies:")
        for module_name, description in modules_to_check:
            try:
                if module_name == 'beautifulsoup4':
                    import bs4
                else:
                    __import__(module_name)
                print(f"   ✅ {module_name} ({description})")
            except ImportError:
                print(f"   ❌ {module_name} ({description}) - Not installed")
        
    elif args.setup_action == 'test':
        print("🧪 Running system tests...")
        
        # Run the test scraper
        try:
            print("   Running test scraper...")
            import subprocess
            result = subprocess.run([sys.executable, 'test_scraper.py'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("   ✅ Test scraper completed successfully")
            else:
                print("   ❌ Test scraper failed")
                if result.stderr:
                    print(f"   Error: {result.stderr}")
        except subprocess.TimeoutExpired:
            print("   ⏱️  Test scraper timed out")
        except Exception as e:
            print(f"   ❌ Error running test: {e}")

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description='Real Estate Scraper CLI Utilities')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Cache management
    cache_parser = subparsers.add_parser('cache', help='Cache management')
    cache_parser.add_argument('cache_action', choices=['stats', 'clear', 'test'],
                             help='Cache action to perform')
    cache_parser.add_argument('--older-than', type=int, 
                             help='Clear cache entries older than X hours')
    
    # Data validation
    validate_parser = subparsers.add_parser('validate', help='Data validation')
    validate_parser.add_argument('validate_action', choices=['test', 'clean'],
                                help='Validation action to perform')
    validate_parser.add_argument('--input-file', 
                                help='Input file for cleaning (CSV/JSON)')
    
    # Performance monitoring
    perf_parser = subparsers.add_parser('performance', help='Performance monitoring')
    perf_parser.add_argument('perf_action', choices=['test', 'report'],
                            help='Performance action to perform')
    
    # Data analysis
    analyze_parser = subparsers.add_parser('analyze', help='Data analysis')
    analyze_parser.add_argument('analyze_action', choices=['demo', 'file'],
                               help='Analysis action to perform')
    analyze_parser.add_argument('--input-file',
                               help='Input file for analysis (CSV/JSON)')
    
    # Setup and diagnostics
    setup_parser = subparsers.add_parser('setup', help='Setup and diagnostics')
    setup_parser.add_argument('setup_action', choices=['check', 'test'],
                             help='Setup action to perform')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    print(f"🏠 Real Estate Scraper CLI - {args.command.upper()}")
    print("=" * 50)
    
    try:
        if args.command == 'cache':
            cache_command(args)
        elif args.command == 'validate':
            validate_command(args)
        elif args.command == 'performance':
            performance_command(args)
        elif args.command == 'analyze':
            analyze_command(args)
        elif args.command == 'setup':
            setup_command(args)
        
        print("\n✅ Command completed successfully!")
        
    except KeyboardInterrupt:
        print("\n❌ Command interrupted by user")
    except Exception as e:
        print(f"\n❌ Command failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()