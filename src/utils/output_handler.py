"""Output handling utilities for exporting scraped data."""

import json
import csv
import sqlite3
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

import pandas as pd

from ..scrapers.base_scraper import Property
from .logger import setup_logger


class OutputHandler:
    """Handle output of scraped real estate data in various formats."""
    
    def __init__(self, config):
        self.config = config
        self.logger = setup_logger("OutputHandler", level=config.log_level)
        
        # Ensure output directory exists
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def save_properties(self, properties: List[Property], filename_prefix: str = "properties") -> str:
        """Save properties in the configured output format."""
        if not properties:
            self.logger.warning("No properties to save")
            return ""
        
        format_method = {
            'csv': self.save_as_csv,
            'json': self.save_as_json,
            'excel': self.save_as_excel,
            'db': self.save_to_database,
            'sqlite': self.save_to_database,
        }
        
        output_format = self.config.output_format.lower()
        
        if output_format not in format_method:
            self.logger.error(f"Unsupported output format: {output_format}")
            return ""
        
        try:
            return format_method[output_format](properties, filename_prefix)
        except Exception as e:
            self.logger.error(f"Error saving properties: {str(e)}")
            return ""
    
    def save_as_csv(self, properties: List[Property], filename_prefix: str = "properties") -> str:
        """Save properties as CSV file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.csv"
        filepath = self.output_dir / filename
        
        # Convert properties to dictionaries
        data = [prop.to_dict() for prop in properties]
        
        if not data:
            self.logger.warning("No data to save")
            return ""
        
        # Get all unique fieldnames
        fieldnames = set()
        for item in data:
            fieldnames.update(item.keys())
        
        fieldnames = sorted(list(fieldnames))
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for item in data:
                # Convert lists to strings for CSV
                row = {}
                for key, value in item.items():
                    if isinstance(value, list):
                        row[key] = '; '.join(str(v) for v in value) if value else ''
                    else:
                        row[key] = value
                writer.writerow(row)
        
        self.logger.info(f"Saved {len(properties)} properties to CSV: {filepath}")
        return str(filepath)
    
    def save_as_json(self, properties: List[Property], filename_prefix: str = "properties") -> str:
        """Save properties as JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.json"
        filepath = self.output_dir / filename
        
        # Convert properties to dictionaries
        data = [prop.to_dict() for prop in properties]
        
        with open(filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"Saved {len(properties)} properties to JSON: {filepath}")
        return str(filepath)
    
    def save_as_excel(self, properties: List[Property], filename_prefix: str = "properties") -> str:
        """Save properties as Excel file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.xlsx"
        filepath = self.output_dir / filename
        
        # Convert properties to dictionaries
        data = [prop.to_dict() for prop in properties]
        
        if not data:
            self.logger.warning("No data to save")
            return ""
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Convert list columns to strings
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].apply(lambda x: '; '.join(str(v) for v in x) if isinstance(x, list) else x)
        
        # Save to Excel
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Properties', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Properties']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        self.logger.info(f"Saved {len(properties)} properties to Excel: {filepath}")
        return str(filepath)
    
    def save_to_database(self, properties: List[Property], filename_prefix: str = "properties") -> str:
        """Save properties to SQLite database."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.db"
        filepath = self.output_dir / filename
        
        conn = sqlite3.connect(filepath)
        cursor = conn.cursor()
        
        try:
            # Create properties table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS properties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    address TEXT,
                    city TEXT,
                    state TEXT,
                    zip_code TEXT,
                    price REAL,
                    bedrooms INTEGER,
                    bathrooms REAL,
                    square_feet INTEGER,
                    lot_size REAL,
                    property_type TEXT,
                    year_built INTEGER,
                    listing_date TEXT,
                    listing_url TEXT,
                    listing_agent TEXT,
                    description TEXT,
                    photos TEXT,
                    features TEXT,
                    scraped_at TEXT
                )
            ''')
            
            # Insert properties
            for prop in properties:
                data = prop.to_dict()
                
                # Convert lists to JSON strings
                photos = json.dumps(data.get('photos', [])) if data.get('photos') else None
                features = json.dumps(data.get('features', [])) if data.get('features') else None
                
                cursor.execute('''
                    INSERT INTO properties (
                        address, city, state, zip_code, price, bedrooms, bathrooms,
                        square_feet, lot_size, property_type, year_built, listing_date,
                        listing_url, listing_agent, description, photos, features, scraped_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data.get('address'),
                    data.get('city'),
                    data.get('state'),
                    data.get('zip_code'),
                    data.get('price'),
                    data.get('bedrooms'),
                    data.get('bathrooms'),
                    data.get('square_feet'),
                    data.get('lot_size'),
                    data.get('property_type'),
                    data.get('year_built'),
                    data.get('listing_date'),
                    data.get('listing_url'),
                    data.get('listing_agent'),
                    data.get('description'),
                    photos,
                    features,
                    data.get('scraped_at')
                ))
            
            conn.commit()
            self.logger.info(f"Saved {len(properties)} properties to database: {filepath}")
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error saving to database: {str(e)}")
            raise
        finally:
            conn.close()
        
        return str(filepath)
    
    def save_summary_report(self, properties: List[Property], filename_prefix: str = "summary") -> str:
        """Generate and save a summary report of the scraped properties."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.txt"
        filepath = self.output_dir / filename
        
        if not properties:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("No properties found.\n")
            return str(filepath)
        
        # Calculate statistics
        stats = self._calculate_statistics(properties)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("REAL ESTATE SCRAPER SUMMARY REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Properties: {len(properties)}\n\n")
            
            # Price statistics
            if stats['price_stats']:
                f.write("PRICE STATISTICS\n")
                f.write("-" * 20 + "\n")
                f.write(f"Average Price: ${stats['price_stats']['mean']:,.2f}\n")
                f.write(f"Median Price: ${stats['price_stats']['median']:,.2f}\n")
                f.write(f"Min Price: ${stats['price_stats']['min']:,.2f}\n")
                f.write(f"Max Price: ${stats['price_stats']['max']:,.2f}\n")
                f.write(f"Properties with Price: {stats['price_stats']['count']}\n\n")
            
            # Location distribution
            if stats['location_stats']:
                f.write("LOCATION DISTRIBUTION\n")
                f.write("-" * 20 + "\n")
                for state, count in stats['location_stats']['states'].items():
                    f.write(f"{state}: {count} properties\n")
                f.write("\nTop Cities:\n")
                for city, count in list(stats['location_stats']['cities'].items())[:10]:
                    f.write(f"  {city}: {count} properties\n")
                f.write("\n")
            
            # Property type distribution
            if stats['type_stats']:
                f.write("PROPERTY TYPE DISTRIBUTION\n")
                f.write("-" * 25 + "\n")
                for prop_type, count in stats['type_stats'].items():
                    f.write(f"{prop_type}: {count} properties\n")
                f.write("\n")
            
            # Bedroom/bathroom statistics
            if stats['bed_bath_stats']:
                f.write("BEDROOM/BATHROOM STATISTICS\n")
                f.write("-" * 25 + "\n")
                if 'bedrooms' in stats['bed_bath_stats']:
                    f.write("Bedrooms:\n")
                    for beds, count in stats['bed_bath_stats']['bedrooms'].items():
                        f.write(f"  {beds} bed: {count} properties\n")
                if 'bathrooms' in stats['bed_bath_stats']:
                    f.write("Bathrooms:\n")
                    for baths, count in stats['bed_bath_stats']['bathrooms'].items():
                        f.write(f"  {baths} bath: {count} properties\n")
                f.write("\n")
            
            # Square feet statistics
            if stats['sqft_stats']:
                f.write("SQUARE FEET STATISTICS\n")
                f.write("-" * 20 + "\n")
                f.write(f"Average: {stats['sqft_stats']['mean']:,.0f} sq ft\n")
                f.write(f"Median: {stats['sqft_stats']['median']:,.0f} sq ft\n")
                f.write(f"Min: {stats['sqft_stats']['min']:,.0f} sq ft\n")
                f.write(f"Max: {stats['sqft_stats']['max']:,.0f} sq ft\n")
                f.write(f"Properties with Sq Ft: {stats['sqft_stats']['count']}\n\n")
        
        self.logger.info(f"Saved summary report: {filepath}")
        return str(filepath)
    
    def _calculate_statistics(self, properties: List[Property]) -> Dict[str, Any]:
        """Calculate statistics for the properties."""
        stats = {}
        
        # Price statistics
        prices = [p.price for p in properties if p.price]
        if prices:
            stats['price_stats'] = {
                'mean': sum(prices) / len(prices),
                'median': sorted(prices)[len(prices) // 2],
                'min': min(prices),
                'max': max(prices),
                'count': len(prices)
            }
        
        # Location statistics
        states = {}
        cities = {}
        for prop in properties:
            if prop.state:
                states[prop.state] = states.get(prop.state, 0) + 1
            if prop.city:
                cities[prop.city] = cities.get(prop.city, 0) + 1
        
        if states or cities:
            stats['location_stats'] = {
                'states': dict(sorted(states.items(), key=lambda x: x[1], reverse=True)),
                'cities': dict(sorted(cities.items(), key=lambda x: x[1], reverse=True))
            }
        
        # Property type statistics
        prop_types = {}
        for prop in properties:
            if prop.property_type:
                prop_types[prop.property_type] = prop_types.get(prop.property_type, 0) + 1
        
        if prop_types:
            stats['type_stats'] = dict(sorted(prop_types.items(), key=lambda x: x[1], reverse=True))
        
        # Bedroom/bathroom statistics
        bedrooms = {}
        bathrooms = {}
        for prop in properties:
            if prop.bedrooms is not None:
                bedrooms[prop.bedrooms] = bedrooms.get(prop.bedrooms, 0) + 1
            if prop.bathrooms is not None:
                bathrooms[prop.bathrooms] = bathrooms.get(prop.bathrooms, 0) + 1
        
        if bedrooms or bathrooms:
            stats['bed_bath_stats'] = {}
            if bedrooms:
                stats['bed_bath_stats']['bedrooms'] = dict(sorted(bedrooms.items()))
            if bathrooms:
                stats['bed_bath_stats']['bathrooms'] = dict(sorted(bathrooms.items()))
        
        # Square feet statistics
        sqfts = [p.square_feet for p in properties if p.square_feet]
        if sqfts:
            stats['sqft_stats'] = {
                'mean': sum(sqfts) / len(sqfts),
                'median': sorted(sqfts)[len(sqfts) // 2],
                'min': min(sqfts),
                'max': max(sqfts),
                'count': len(sqfts)
            }
        
        return stats
    
    def load_properties_from_json(self, filepath: str) -> List[Property]:
        """Load properties from a JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            properties = []
            for item in data:
                # Convert back to Property object
                prop = Property(
                    address=item.get('address', ''),
                    city=item.get('city', ''),
                    state=item.get('state', ''),
                    zip_code=item.get('zip_code', ''),
                    price=item.get('price'),
                    bedrooms=item.get('bedrooms'),
                    bathrooms=item.get('bathrooms'),
                    square_feet=item.get('square_feet'),
                    lot_size=item.get('lot_size'),
                    property_type=item.get('property_type'),
                    year_built=item.get('year_built'),
                    listing_url=item.get('listing_url'),
                    listing_agent=item.get('listing_agent'),
                    description=item.get('description'),
                    photos=item.get('photos', []),
                    features=item.get('features', [])
                )
                
                # Parse dates
                if item.get('listing_date'):
                    try:
                        prop.listing_date = datetime.fromisoformat(item['listing_date'])
                    except:
                        pass
                
                if item.get('scraped_at'):
                    try:
                        prop.scraped_at = datetime.fromisoformat(item['scraped_at'])
                    except:
                        pass
                
                properties.append(prop)
            
            self.logger.info(f"Loaded {len(properties)} properties from JSON: {filepath}")
            return properties
            
        except Exception as e:
            self.logger.error(f"Error loading properties from JSON: {str(e)}")
            return []