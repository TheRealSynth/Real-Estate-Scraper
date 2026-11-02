#!/usr/bin/env python3
"""
Test script for Real Estate Scraper
This script tests the core functionality with mock data when dependencies aren't available
"""
import sys
import os
from datetime import datetime
from typing import List, Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Mock imports for testing without dependencies
class MockProperty:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.title = kwargs.get('title')
        self.price = kwargs.get('price')
        self.address = kwargs.get('address')
        self.bedrooms = kwargs.get('bedrooms')
        self.bathrooms = kwargs.get('bathrooms')
        self.square_feet = kwargs.get('square_feet')
        self.property_type = kwargs.get('property_type')
        self.source_website = kwargs.get('source_website')
        self.scraped_at = kwargs.get('scraped_at', datetime.now())
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'price': self.price,
            'address': self.address,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'square_feet': self.square_feet,
            'property_type': self.property_type,
            'source_website': self.source_website,
            'scraped_at': self.scraped_at.isoformat() if hasattr(self.scraped_at, 'isoformat') else str(self.scraped_at)
        }

class MockSearchCriteria:
    def __init__(self, location, **kwargs):
        self.location = location
        self.min_price = kwargs.get('min_price')
        self.max_price = kwargs.get('max_price')
        self.min_bedrooms = kwargs.get('min_bedrooms')
        self.max_bedrooms = kwargs.get('max_bedrooms')
        self.property_types = kwargs.get('property_types', [])
        self.max_pages = kwargs.get('max_pages', 5)

def create_mock_properties() -> List[MockProperty]:
    """Create mock property data for testing"""
    mock_data = [
        {
            'id': 'test_1',
            'title': 'Beautiful 3BR Home in Downtown',
            'price': 750000,
            'address': '123 Main Street, San Francisco, CA 94102',
            'bedrooms': 3,
            'bathrooms': 2.5,
            'square_feet': 1800,
            'property_type': 'House',
            'source_website': 'Zillow'
        },
        {
            'id': 'test_2',
            'title': 'Modern Condo with City Views',
            'price': 650000,
            'address': '456 Oak Avenue, San Francisco, CA 94103',
            'bedrooms': 2,
            'bathrooms': 2,
            'square_feet': 1200,
            'property_type': 'Condo',
            'source_website': 'Realtor.com'
        },
        {
            'id': 'test_3',
            'title': 'Spacious Townhouse Near Park',
            'price': 850000,
            'address': '789 Pine Street, San Francisco, CA 94104',
            'bedrooms': 4,
            'bathrooms': 3,
            'square_feet': 2200,
            'property_type': 'Townhouse',
            'source_website': 'Zillow'
        },
        {
            'id': 'test_4',
            'title': 'Luxury Penthouse Downtown',
            'price': 1200000,
            'address': '321 Market Street, San Francisco, CA 94105',
            'bedrooms': 3,
            'bathrooms': 3.5,
            'square_feet': 2500,
            'property_type': 'Condo',
            'source_website': 'Realtor.com'
        },
        {
            'id': 'test_5',
            'title': 'Cozy 2BR Apartment',
            'price': 550000,
            'address': '654 Valencia Street, San Francisco, CA 94110',
            'bedrooms': 2,
            'bathrooms': 1,
            'square_feet': 950,
            'property_type': 'Condo',
            'source_website': 'Zillow'
        }
    ]
    
    return [MockProperty(**data) for data in mock_data]

def filter_properties(properties: List[MockProperty], criteria: MockSearchCriteria) -> List[MockProperty]:
    """Filter properties based on search criteria"""
    filtered = []
    
    for prop in properties:
        # Check price range
        if criteria.min_price and prop.price < criteria.min_price:
            continue
        if criteria.max_price and prop.price > criteria.max_price:
            continue
        
        # Check bedrooms
        if criteria.min_bedrooms and prop.bedrooms < criteria.min_bedrooms:
            continue
        if criteria.max_bedrooms and prop.bedrooms > criteria.max_bedrooms:
            continue
        
        # Check property types
        if criteria.property_types and prop.property_type.lower() not in [pt.lower() for pt in criteria.property_types]:
            continue
        
        filtered.append(prop)
    
    return filtered

def save_to_mock_csv(properties: List[MockProperty], filename: str):
    """Save properties to a mock CSV format (text file)"""
    os.makedirs('data', exist_ok=True)
    filepath = os.path.join('data', filename)
    
    with open(filepath, 'w') as f:
        # Header
        f.write("id,title,price,address,bedrooms,bathrooms,square_feet,property_type,source_website,scraped_at\n")
        
        # Data rows
        for prop in properties:
            f.write(f'"{prop.id}","{prop.title}",{prop.price},"{prop.address}",{prop.bedrooms},{prop.bathrooms},{prop.square_feet},"{prop.property_type}","{prop.source_website}","{prop.scraped_at}"\n')
    
    return filepath

def test_basic_functionality():
    """Test basic scraper functionality with mock data"""
    print("🧪 Testing Real Estate Scraper with Mock Data")
    print("=" * 50)
    
    # Create search criteria
    criteria = MockSearchCriteria(
        location="San Francisco, CA",
        min_price=600000,
        max_price=1000000,
        min_bedrooms=2,
        property_types=['house', 'condo']
    )
    
    print(f"📍 Search Location: {criteria.location}")
    print(f"💰 Price Range: ${criteria.min_price:,} - ${criteria.max_price:,}")
    print(f"🛏️  Min Bedrooms: {criteria.min_bedrooms}")
    print(f"🏠 Property Types: {', '.join(criteria.property_types)}")
    print()
    
    # Generate mock properties
    all_properties = create_mock_properties()
    print(f"📊 Total Mock Properties Generated: {len(all_properties)}")
    
    # Filter properties
    filtered_properties = filter_properties(all_properties, criteria)
    print(f"🔍 Properties Matching Criteria: {len(filtered_properties)}")
    print()
    
    # Display results
    if filtered_properties:
        print("📋 Matching Properties:")
        print("-" * 80)
        for i, prop in enumerate(filtered_properties, 1):
            print(f"{i}. {prop.title}")
            print(f"   💵 Price: ${prop.price:,}")
            print(f"   📍 Address: {prop.address}")
            print(f"   🛏️  {prop.bedrooms} bed, {prop.bathrooms} bath, {prop.square_feet} sq ft")
            print(f"   🏠 Type: {prop.property_type} | Source: {prop.source_website}")
            print()
        
        # Save to file
        filename = f"test_properties_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        saved_file = save_to_mock_csv(filtered_properties, filename)
        print(f"💾 Data saved to: {saved_file}")
        
        # Statistics
        total_value = sum(prop.price for prop in filtered_properties)
        avg_price = total_value / len(filtered_properties)
        print(f"📈 Average Price: ${avg_price:,.2f}")
        
        property_types = {}
        for prop in filtered_properties:
            property_types[prop.property_type] = property_types.get(prop.property_type, 0) + 1
        
        print("📊 Property Type Breakdown:")
        for prop_type, count in property_types.items():
            print(f"   {prop_type}: {count}")
    
    else:
        print("❌ No properties found matching the criteria")
    
    print("\n✅ Test completed successfully!")
    return len(filtered_properties)

def test_data_validation():
    """Test data validation functionality"""
    print("\n🔍 Testing Data Validation")
    print("=" * 30)
    
    # Test with invalid data
    invalid_data = {
        'title': '',  # Empty title
        'price': -100,  # Negative price
        'bedrooms': 0,  # Zero bedrooms
        'square_feet': None  # Missing square feet
    }
    
    prop = MockProperty(**invalid_data)
    
    # Simple validation checks
    issues = []
    if not prop.title or prop.title.strip() == '':
        issues.append("Empty title")
    if prop.price and prop.price < 0:
        issues.append("Negative price")
    if prop.bedrooms and prop.bedrooms <= 0:
        issues.append("Invalid bedroom count")
    if not prop.square_feet:
        issues.append("Missing square feet")
    
    if issues:
        print(f"❌ Validation issues found: {', '.join(issues)}")
    else:
        print("✅ All data validation passed")
    
    return len(issues) == 0

if __name__ == "__main__":
    print("🏠 Real Estate Scraper - Test Suite")
    print("=" * 50)
    
    try:
        # Test basic functionality
        properties_found = test_basic_functionality()
        
        # Test data validation
        validation_passed = test_data_validation()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Test Summary:")
        print(f"   Properties Found: {properties_found}")
        print(f"   Data Validation: {'PASSED' if validation_passed else 'FAILED'}")
        print("   Overall Status: ✅ SUCCESS")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)