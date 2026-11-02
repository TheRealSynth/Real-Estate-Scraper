# 🏠 Real Estate Scraper

A comprehensive Python-based real estate scraper that extracts property listings from multiple real estate websites including Zillow, Realtor.com, and more. The scraper provides clean, standardized data output in multiple formats (CSV, JSON, Excel, SQLite) with advanced filtering and data processing capabilities.

## ✨ Features

- **Multi-Site Scraping**: Supports Zillow, Realtor.com with extensible architecture for additional sites
- **Multiple Output Formats**: Export data as CSV, JSON, Excel, or SQLite database
- **Data Processing**: Automatic data cleaning, standardization, and deduplication
- **Advanced Filtering**: Filter by price, bedrooms, bathrooms, square footage, property type, and location
- **Configurable**: Environment-based configuration with sensible defaults
- **CLI Interface**: Easy-to-use command-line interface with comprehensive options
- **Logging**: Colored logging with configurable levels
- **Rate Limiting**: Respectful scraping with configurable delays and concurrent request limits
- **Error Handling**: Robust error handling with retry mechanisms

## 🚀 Quick Start

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Real-Estate-Scraper
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up configuration** (optional):
   ```bash
   cp .env.example .env
   # Edit .env with your preferred settings
   ```

### Basic Usage

**Scrape properties in a specific location**:
```bash
python scraper.py scrape --location "Austin, TX"
```

**Scrape with specific criteria**:
```bash
python scraper.py scrape --location "Seattle, WA" --min-price 300000 --max-price 800000 --bedrooms 2 --output-format json
```

**Scrape from specific sites only**:
```bash
python scraper.py scrape --location "Miami, FL" --sites zillow realtor
```

## 📖 Usage Guide

### Command Line Interface

The scraper provides several commands:

#### `scrape` - Scrape Property Listings

```bash
python scraper.py scrape [OPTIONS]
```

**Options**:
- `--location, -l`: Location to search (required) - city, state, or zip code
- `--sites, -s`: Sites to scrape from (`zillow`, `realtor`, `all`) - default: `all`
- `--min-price`: Minimum price filter
- `--max-price`: Maximum price filter  
- `--bedrooms`: Minimum number of bedrooms
- `--bathrooms`: Minimum number of bathrooms
- `--property-type`: Property type (`house`, `condo`, `townhouse`, `apartment`)
- `--min-sqft`: Minimum square footage
- `--max-sqft`: Maximum square footage
- `--output-format`: Output format (`csv`, `json`, `excel`, `db`)
- `--output-dir`: Output directory
- `--no-filter`: Skip additional filtering of results

**Examples**:
```bash
# Basic search
python scraper.py scrape -l "Denver, CO"

# Advanced filtering
python scraper.py scrape -l "Los Angeles, CA" --min-price 500000 --max-price 1000000 --bedrooms 3 --bathrooms 2 --property-type house --output-format excel

# Scrape specific sites
python scraper.py scrape -l "New York, NY" --sites zillow --min-sqft 1000
```

#### `convert` - Convert Existing Data

Convert and filter existing JSON property data:

```bash
python scraper.py convert --input-file data.json --output-format csv --min-price 200000
```

#### `analyze` - Analyze Property Data

Generate statistical analysis of property data:

```bash
python scraper.py analyze --input-file data.json
```

#### `config` - Show Configuration

Display current configuration settings:

```bash
python scraper.py config
```

### Configuration

The scraper can be configured via environment variables or a `.env` file:

```env
# Scraping behavior
SCRAPER_DELAY=2                    # Delay between requests (seconds)
MAX_CONCURRENT_REQUESTS=3          # Maximum concurrent requests
USER_AGENT_ROTATE=true             # Rotate user agents
HEADLESS_BROWSER=true              # Run browser in headless mode

# Output settings
OUTPUT_FORMAT=csv                  # Default output format
OUTPUT_DIR=./data                  # Output directory
LOG_LEVEL=INFO                     # Logging level

# Database
DATABASE_URL=sqlite:///real_estate.db

# API Keys (optional)
ZILLOW_API_KEY=your_api_key_here
REALTOR_API_KEY=your_api_key_here
```

## 📊 Data Structure

The scraper extracts the following property information:

- **Address Information**: Street address, city, state, ZIP code
- **Property Details**: Price, bedrooms, bathrooms, square footage, lot size
- **Property Metadata**: Property type, year built, listing date, listing agent
- **Additional Data**: Description, photos, features, listing URL
- **Scraping Metadata**: Scraped timestamp

## 🛠️ Architecture

The project is structured as follows:

```
Real-Estate-Scraper/
├── src/
│   ├── scrapers/           # Site-specific scrapers
│   │   ├── base_scraper.py # Base scraper class
│   │   ├── zillow_scraper.py
│   │   └── realtor_scraper.py
│   ├── utils/              # Utility modules
│   │   ├── config.py       # Configuration management
│   │   ├── logger.py       # Logging setup
│   │   ├── data_processor.py # Data cleaning & processing
│   │   └── output_handler.py # Output format handlers
│   └── main.py             # CLI interface
├── tests/                  # Test files
├── config/                 # Configuration files
├── data/                   # Output data directory
├── logs/                   # Log files
├── requirements.txt        # Python dependencies
├── .env.example           # Example environment file
└── scraper.py             # Entry point script
```

### Key Components

1. **Base Scraper**: Abstract base class providing common scraping functionality
2. **Site Scrapers**: Specific implementations for each real estate website
3. **Data Processor**: Handles data cleaning, validation, and standardization
4. **Output Handler**: Manages multiple output formats and file generation
5. **Configuration**: Environment-based configuration management
6. **CLI Interface**: User-friendly command-line interface

## 🔧 Extending the Scraper

### Adding New Sites

To add support for a new real estate website:

1. Create a new scraper class inheriting from `BaseScraper`
2. Implement the required abstract methods:
   - `scrape_listings(search_params)`: Extract property listings
   - `scrape_property_details(property_url)`: Get detailed property info
3. Add the scraper to the main scraper registry in `src/main.py`

Example:
```python
from .base_scraper import BaseScraper, Property

class NewSiteScraper(BaseScraper):
    def scrape_listings(self, search_params):
        # Implementation here
        pass
    
    def scrape_property_details(self, property_url):
        # Implementation here
        pass
```

### Adding Output Formats

To add a new output format:

1. Add a new method to the `OutputHandler` class
2. Update the format mapping in `save_properties()`
3. Add the new format to CLI choices

## ⚠️ Important Notes

### Legal and Ethical Considerations

- **Respect robots.txt**: Always check and respect website robots.txt files
- **Rate Limiting**: The scraper includes built-in delays and rate limiting
- **Terms of Service**: Ensure compliance with website terms of service
- **Personal Use**: This tool is intended for personal, educational, or research purposes

### Technical Considerations

- **Dynamic Content**: Some sites use JavaScript; Selenium is included for such cases
- **Anti-Bot Protection**: Websites may implement anti-bot measures
- **Data Changes**: Website structures change; scrapers may need updates
- **IP Blocking**: Use appropriate delays and consider proxy rotation for large-scale scraping

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## 📄 License

This project is provided as-is for educational and research purposes. Please ensure compliance with all applicable laws and website terms of service.

## 🆘 Troubleshooting

### Common Issues

1. **No data found**: Check if the website structure has changed
2. **Rate limiting**: Increase delays in configuration
3. **ChromeDriver issues**: Ensure Chrome is installed and updated
4. **Dependency errors**: Verify all requirements are installed

### Getting Help

- Check the logs in the `logs/` directory for detailed error information
- Use `--log-level DEBUG` for verbose logging
- Review the configuration with `python scraper.py config`

---

**Happy scraping! 🏠✨**