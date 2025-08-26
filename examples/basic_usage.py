#!/usr/bin/env python3
"""
Basic usage examples for the Real Estate Scraper
"""
import sys
import os

# Add parent directory to path to import scraper modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def example_1_basic_search():
    """Example 1: Basic property search"""
    print("🏠 Example 1: Basic Property Search")
    print("=" * 40)
    
    # This example demonstrates how to use the scraper programmatically
    # Note: This would require the dependencies to be installed
    
    try:
        from src.models import SearchCriteria
        from src.data_manager import DataManager
        from scrapers.zillow_scraper import ZillowScraper
        
        # Create search criteria
        criteria = SearchCriteria(
            location="Austin, TX",
            min_price=300000,
            max_price=600000,
            min_bedrooms=2,
            max_bedrooms=4,
            property_types=['house', 'condo']
        )
        
        print(f"📍 Searching in: {criteria.location}")
        print(f"💰 Price range: ${criteria.min_price:,} - ${criteria.max_price:,}")
        print(f"🛏️  Bedrooms: {criteria.min_bedrooms} - {criteria.max_bedrooms}")
        print(f"🏠 Property types: {', '.join(criteria.property_types)}")
        
        # Initialize scraper
        with ZillowScraper(use_selenium=True) as scraper:
            properties = scraper.scrape_property_list(criteria)
            
            print(f"\n✅ Found {len(properties)} properties")
            
            # Save results
            data_manager = DataManager()
            saved_file = data_manager.save_properties(properties, "austin_search")
            print(f"💾 Data saved to: {saved_file}")
            
    except ImportError as e:
        print(f"❌ Dependencies not available: {e}")
        print("💡 Install dependencies with: pip install -r requirements.txt")
        print("🔧 Or run the test script: python test_scraper.py")

def example_2_multiple_scrapers():
    """Example 2: Using multiple scrapers"""
    print("\n🌐 Example 2: Multiple Scrapers")
    print("=" * 40)
    
    try:
        from src.models import SearchCriteria
        from scrapers.zillow_scraper import ZillowScraper
        from scrapers.realtor_scraper import RealtorScraper
        
        criteria = SearchCriteria(
            location="Denver, CO",
            min_price=400000,
            max_price=800000,
            property_types=['house']
        )
        
        all_properties = []
        scrapers = [
            ('Zillow', ZillowScraper),
            ('Realtor.com', RealtorScraper)
        ]
        
        for name, scraper_class in scrapers:
            print(f"🔍 Scraping {name}...")
            
            with scraper_class(use_selenium=True) as scraper:
                properties = scraper.scrape_property_list(criteria)
                all_properties.extend(properties)
                print(f"   Found {len(properties)} properties")
        
        print(f"\n📊 Total properties from all sources: {len(all_properties)}")
        
    except ImportError as e:
        print(f"❌ Dependencies not available: {e}")

def example_3_data_analysis():
    """Example 3: Data analysis and statistics"""
    print("\n📈 Example 3: Data Analysis")
    print("=" * 40)
    
    # Mock data for demonstration
    mock_properties = [
        {'price': 500000, 'bedrooms': 3, 'square_feet': 1800, 'property_type': 'house'},
        {'price': 650000, 'bedrooms': 4, 'square_feet': 2200, 'property_type': 'house'},
        {'price': 450000, 'bedrooms': 2, 'square_feet': 1200, 'property_type': 'condo'},
        {'price': 750000, 'bedrooms': 3, 'square_feet': 1600, 'property_type': 'condo'},
        {'price': 850000, 'bedrooms': 4, 'square_feet': 2500, 'property_type': 'townhouse'},
    ]
    
    # Calculate statistics
    prices = [p['price'] for p in mock_properties]
    avg_price = sum(prices) / len(prices)
    min_price = min(prices)
    max_price = max(prices)
    
    print(f"📊 Analysis of {len(mock_properties)} properties:")
    print(f"💰 Average price: ${avg_price:,.2f}")
    print(f"📉 Min price: ${min_price:,}")
    print(f"📈 Max price: ${max_price:,}")
    
    # Price per square foot
    price_per_sqft = []
    for prop in mock_properties:
        if prop['square_feet']:
            ppsf = prop['price'] / prop['square_feet']
            price_per_sqft.append(ppsf)
    
    if price_per_sqft:
        avg_ppsf = sum(price_per_sqft) / len(price_per_sqft)
        print(f"🏠 Average price per sq ft: ${avg_ppsf:.2f}")
    
    # Property type distribution
    type_counts = {}
    for prop in mock_properties:
        prop_type = prop['property_type']
        type_counts[prop_type] = type_counts.get(prop_type, 0) + 1
    
    print("\n🏘️  Property type distribution:")
    for prop_type, count in type_counts.items():
        percentage = (count / len(mock_properties)) * 100
        print(f"   {prop_type}: {count} ({percentage:.1f}%)")

def example_4_filtering_and_validation():
    """Example 4: Data filtering and validation"""
    print("\n🔍 Example 4: Data Filtering & Validation")
    print("=" * 40)
    
    # Mock property data with some invalid entries
    raw_properties = [
        {'title': 'Beautiful Home', 'price': 500000, 'bedrooms': 3, 'address': '123 Main St, Austin, TX'},
        {'title': '', 'price': -50000, 'bedrooms': 0, 'address': ''},  # Invalid
        {'title': 'Luxury Condo', 'price': 750000, 'bedrooms': 2, 'address': '456 Oak Ave, Austin, TX'},
        {'title': 'Nice House', 'price': 0, 'bedrooms': 5, 'address': 'No Address'},  # Invalid price
        {'title': 'Townhouse', 'price': 600000, 'bedrooms': 3, 'address': '789 Pine St, Austin, TX'},
    ]
    
    # Simple validation
    valid_properties = []
    invalid_count = 0
    
    for prop in raw_properties:
        issues = []
        
        # Check required fields
        if not prop.get('title') or not prop['title'].strip():
            issues.append("Missing title")
        
        if not prop.get('price') or prop['price'] <= 0:
            issues.append("Invalid price")
        
        if not prop.get('bedrooms') or prop['bedrooms'] <= 0:
            issues.append("Invalid bedrooms")
        
        if not prop.get('address') or len(prop['address']) < 10:
            issues.append("Invalid address")
        
        if issues:
            print(f"❌ Invalid property: {', '.join(issues)}")
            invalid_count += 1
        else:
            valid_properties.append(prop)
            print(f"✅ Valid: {prop['title']}")
    
    print(f"\n📊 Validation Summary:")
    print(f"   Valid properties: {len(valid_properties)}")
    print(f"   Invalid properties: {invalid_count}")
    print(f"   Success rate: {(len(valid_properties) / len(raw_properties)) * 100:.1f}%")

def example_5_custom_filters():
    """Example 5: Custom filtering logic"""
    print("\n🎯 Example 5: Custom Filtering")
    print("=" * 40)
    
    # Mock property data
    properties = [
        {'price': 400000, 'bedrooms': 2, 'square_feet': 1200, 'year_built': 2020, 'city': 'Austin'},
        {'price': 600000, 'bedrooms': 3, 'square_feet': 1800, 'year_built': 2015, 'city': 'Austin'},
        {'price': 800000, 'bedrooms': 4, 'square_feet': 2400, 'year_built': 2010, 'city': 'Austin'},
        {'price': 550000, 'bedrooms': 3, 'square_feet': 1600, 'year_built': 2018, 'city': 'Austin'},
        {'price': 750000, 'bedrooms': 3, 'square_feet': 2000, 'year_built': 2022, 'city': 'Austin'},
    ]
    
    print(f"🏠 Starting with {len(properties)} properties")
    
    # Filter 1: Price per square foot under $350
    filtered1 = []
    for prop in properties:
        ppsf = prop['price'] / prop['square_feet']
        if ppsf <= 350:
            filtered1.append(prop)
    
    print(f"💰 After price/sqft filter (≤$350): {len(filtered1)} properties")
    
    # Filter 2: Built after 2015
    filtered2 = []
    for prop in filtered1:
        if prop['year_built'] > 2015:
            filtered2.append(prop)
    
    print(f"🏗️  After year built filter (>2015): {len(filtered2)} properties")
    
    # Filter 3: At least 3 bedrooms
    filtered3 = []
    for prop in filtered2:
        if prop['bedrooms'] >= 3:
            filtered3.append(prop)
    
    print(f"🛏️  After bedroom filter (≥3): {len(filtered3)} properties")
    
    # Show final results
    if filtered3:
        print("\n🎯 Final filtered properties:")
        for i, prop in enumerate(filtered3, 1):
            ppsf = prop['price'] / prop['square_feet']
            print(f"   {i}. ${prop['price']:,} | {prop['bedrooms']}BR | {prop['square_feet']}sqft | ${ppsf:.0f}/sqft | {prop['year_built']}")

if __name__ == "__main__":
    print("🏠 Real Estate Scraper - Usage Examples")
    print("=" * 50)
    
    # Run all examples
    example_1_basic_search()
    example_2_multiple_scrapers()
    example_3_data_analysis()
    example_4_filtering_and_validation()
    example_5_custom_filters()
    
    print("\n" + "=" * 50)
    print("✅ All examples completed!")
    print("\n💡 Tips:")
    print("   - Install dependencies: pip install -r requirements.txt")
    print("   - Run main scraper: python main.py 'Your City, State'")
    print("   - Test functionality: python test_scraper.py")
    print("   - Check documentation: README.md")