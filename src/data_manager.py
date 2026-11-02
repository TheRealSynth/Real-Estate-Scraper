"""
Data management for scraped properties
"""
import os
import csv
import json
import sqlite3
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime
import logging

from .models import Property
from config.settings import OUTPUT_DIR, OUTPUT_FORMAT, DATABASE_URL

class DataManager:
    """Manage storage and export of scraped property data"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ensure_output_directory()
    
    def ensure_output_directory(self):
        """Ensure output directory exists"""
        os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    def save_properties(self, properties: List[Property], filename_prefix: str = "properties") -> str:
        """Save properties to the configured output format"""
        if not properties:
            self.logger.warning("No properties to save")
            return ""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if OUTPUT_FORMAT.lower() == 'csv':
            return self.save_to_csv(properties, f"{filename_prefix}_{timestamp}.csv")
        elif OUTPUT_FORMAT.lower() == 'json':
            return self.save_to_json(properties, f"{filename_prefix}_{timestamp}.json")
        elif OUTPUT_FORMAT.lower() == 'database':
            return self.save_to_database(properties)
        else:
            self.logger.error(f"Unsupported output format: {OUTPUT_FORMAT}")
            return ""
    
    def save_to_csv(self, properties: List[Property], filename: str) -> str:
        """Save properties to CSV file"""
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        try:
            # Convert properties to dictionaries
            property_dicts = [prop.to_dict() for prop in properties]
            
            # Create DataFrame
            df = pd.DataFrame(property_dicts)
            
            # Save to CSV
            df.to_csv(filepath, index=False, encoding='utf-8')
            
            self.logger.info(f"Saved {len(properties)} properties to {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error saving to CSV: {str(e)}")
            return ""
    
    def save_to_json(self, properties: List[Property], filename: str) -> str:
        """Save properties to JSON file"""
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        try:
            # Convert properties to dictionaries
            property_dicts = [prop.to_dict() for prop in properties]
            
            # Save to JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'properties': property_dicts,
                    'total_count': len(properties),
                    'scraped_at': datetime.now().isoformat(),
                    'metadata': {
                        'scraper_version': '1.0',
                        'format': 'json'
                    }
                }, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved {len(properties)} properties to {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error saving to JSON: {str(e)}")
            return ""
    
    def save_to_database(self, properties: List[Property]) -> str:
        """Save properties to SQLite database"""
        try:
            # Create database connection
            db_path = DATABASE_URL.replace('sqlite:///', '')
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create table if not exists
            self._create_properties_table(cursor)
            
            # Insert properties
            for prop in properties:
                self._insert_property(cursor, prop)
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Saved {len(properties)} properties to database {db_path}")
            return db_path
            
        except Exception as e:
            self.logger.error(f"Error saving to database: {str(e)}")
            return ""
    
    def _create_properties_table(self, cursor):
        """Create properties table in database"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS properties (
                id TEXT PRIMARY KEY,
                title TEXT,
                price REAL,
                price_currency TEXT,
                address TEXT,
                city TEXT,
                state TEXT,
                zip_code TEXT,
                country TEXT,
                bedrooms INTEGER,
                bathrooms REAL,
                square_feet REAL,
                lot_size REAL,
                year_built INTEGER,
                property_type TEXT,
                listing_agent TEXT,
                listing_agency TEXT,
                listing_date TEXT,
                days_on_market INTEGER,
                mls_number TEXT,
                features TEXT,
                amenities TEXT,
                description TEXT,
                images TEXT,
                virtual_tour_url TEXT,
                source_url TEXT,
                source_website TEXT,
                scraped_at TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
    def _insert_property(self, cursor, property_obj: Property):
        """Insert a single property into the database"""
        # Generate ID if not provided
        if not property_obj.id:
            property_obj.id = f"{property_obj.source_website}_{hash(property_obj.source_url or property_obj.address)}"
        
        cursor.execute('''
            INSERT OR REPLACE INTO properties (
                id, title, price, price_currency, address, city, state, zip_code, country,
                bedrooms, bathrooms, square_feet, lot_size, year_built, property_type,
                listing_agent, listing_agency, listing_date, days_on_market, mls_number,
                features, amenities, description, images, virtual_tour_url,
                source_url, source_website, scraped_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            property_obj.id,
            property_obj.title,
            property_obj.price,
            property_obj.price_currency,
            property_obj.address,
            property_obj.city,
            property_obj.state,
            property_obj.zip_code,
            property_obj.country,
            property_obj.bedrooms,
            property_obj.bathrooms,
            property_obj.square_feet,
            property_obj.lot_size,
            property_obj.year_built,
            property_obj.property_type,
            property_obj.listing_agent,
            property_obj.listing_agency,
            property_obj.listing_date.isoformat() if property_obj.listing_date else None,
            property_obj.days_on_market,
            property_obj.mls_number,
            json.dumps(property_obj.features) if property_obj.features else None,
            json.dumps(property_obj.amenities) if property_obj.amenities else None,
            property_obj.description,
            json.dumps(property_obj.images) if property_obj.images else None,
            property_obj.virtual_tour_url,
            property_obj.source_url,
            property_obj.source_website,
            property_obj.scraped_at.isoformat()
        ))
    
    def load_properties_from_database(self, limit: int = None) -> List[Property]:
        """Load properties from database"""
        try:
            db_path = DATABASE_URL.replace('sqlite:///', '')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            query = "SELECT * FROM properties ORDER BY scraped_at DESC"
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Get column names
            columns = [description[0] for description in cursor.description]
            
            properties = []
            for row in rows:
                property_dict = dict(zip(columns, row))
                
                # Convert JSON fields back to lists
                if property_dict.get('features'):
                    property_dict['features'] = json.loads(property_dict['features'])
                
                if property_dict.get('amenities'):
                    property_dict['amenities'] = json.loads(property_dict['amenities'])
                
                if property_dict.get('images'):
                    property_dict['images'] = json.loads(property_dict['images'])
                
                # Convert datetime strings
                if property_dict.get('scraped_at'):
                    property_dict['scraped_at'] = datetime.fromisoformat(property_dict['scraped_at'])
                
                if property_dict.get('listing_date'):
                    property_dict['listing_date'] = datetime.fromisoformat(property_dict['listing_date'])
                
                # Create Property object (removing database-specific fields)
                property_dict.pop('created_at', None)
                properties.append(Property(**property_dict))
            
            conn.close()
            return properties
            
        except Exception as e:
            self.logger.error(f"Error loading from database: {str(e)}")
            return []
    
    def get_property_statistics(self) -> Dict[str, Any]:
        """Get statistics about scraped properties"""
        try:
            db_path = DATABASE_URL.replace('sqlite:///', '')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Total count
            cursor.execute("SELECT COUNT(*) FROM properties")
            total_count = cursor.fetchone()[0]
            
            # Average price
            cursor.execute("SELECT AVG(price) FROM properties WHERE price IS NOT NULL")
            avg_price = cursor.fetchone()[0]
            
            # Price range
            cursor.execute("SELECT MIN(price), MAX(price) FROM properties WHERE price IS NOT NULL")
            min_price, max_price = cursor.fetchone()
            
            # Properties by source
            cursor.execute("SELECT source_website, COUNT(*) FROM properties GROUP BY source_website")
            sources = dict(cursor.fetchall())
            
            # Properties by type
            cursor.execute("SELECT property_type, COUNT(*) FROM properties GROUP BY property_type")
            types = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                'total_properties': total_count,
                'average_price': avg_price,
                'price_range': {'min': min_price, 'max': max_price},
                'sources': sources,
                'property_types': types
            }
            
        except Exception as e:
            self.logger.error(f"Error getting statistics: {str(e)}")
            return {}