# Real Estate Scraper

A comprehensive Python web scraper for collecting real estate property data from multiple sources including Zillow and Realtor.com. This tool provides a robust framework for gathering property listings with detailed information and flexible export options.

## Features

- **Multi-site Scraping**: Support for Zillow and Realtor.com
- **Advanced Filtering**: Price range, bedrooms, bathrooms, property types
- **Multiple Output Formats**: CSV, JSON, and SQLite database
- **Robust Architecture**: Built with error handling, rate limiting, and logging
- **Selenium Support**: Handles JavaScript-heavy sites
- **Data Management**: Built-in statistics and data analysis tools
- **Command Line Interface**: Easy-to-use CLI for batch operations

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Real-Estate-Scraper
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Install Chrome/Firefox driver (for Selenium):
- Chrome: The script automatically downloads ChromeDriver using webdriver-manager
- Firefox: Install geckodriver manually or let webdriver-manager handle it

## Usage

### Basic Usage

Search for properties in a specific location:
```bash
python main.py "San Francisco, CA"
```

### Advanced Usage

Use filters and specify scrapers:
```bash
python main.py "New York, NY" \
    --min-price 500000 \
    --max-price 2000000 \
    --min-bedrooms 2 \
    --max-bedrooms 4 \
    --property-types house condo \
    --scrapers zillow realtor \
    --max-pages 10 \
    --output-format csv
```

### Command Line Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `location` | Location to search (required) | `"Los Angeles, CA"` |
| `--min-price` | Minimum price filter | `--min-price 300000` |
| `--max-price` | Maximum price filter | `--max-price 1000000` |
| `--min-bedrooms` | Minimum bedrooms | `--min-bedrooms 2` |
| `--max-bedrooms` | Maximum bedrooms | `--max-bedrooms 5` |
| `--min-bathrooms` | Minimum bathrooms | `--min-bathrooms 1.5` |
| `--max-bathrooms` | Maximum bathrooms | `--max-bathrooms 3` |
| `--property-types` | Property types to include | `--property-types house condo` |
| `--max-pages` | Maximum pages per site | `--max-pages 20` |
| `--scrapers` | Specific scrapers to use | `--scrapers zillow` |
| `--output-format` | Output format | `--output-format json` |
| `--output-prefix` | Output file prefix | `--output-prefix "sf_properties"` |
| `--stats` | Show database statistics | `--stats` |
| `--verbose` | Enable verbose logging | `--verbose` |

### Examples

1. **Basic search for apartments in Seattle:**
```bash
python main.py "Seattle, WA" --property-types condo --max-pages 5
```

2. **Search for luxury homes in Miami:**
```bash
python main.py "Miami, FL" --min-price 1000000 --property-types house --output-format database
```

3. **Budget-friendly condos in Austin:**
```bash
python main.py "Austin, TX" --max-price 400000 --property-types condo --min-bedrooms 1
```

4. **Show existing data statistics:**
```bash
python main.py --stats
```

## Configuration

Edit `config/settings.py` to customize default behavior:

```python
# General settings
USER_AGENT = "Your User Agent String"
REQUEST_DELAY = 2  # Delay between requests
MAX_RETRIES = 3
TIMEOUT = 30

# Output settings
OUTPUT_FORMAT = 'csv'  # Options: 'csv', 'json', 'database'
OUTPUT_DIR = 'data'

# Scraping settings
MAX_PAGES = 50
MAX_PROPERTIES = 1000

# Rate limiting
REQUESTS_PER_MINUTE = 30
```

## Output Data Structure

Each property includes the following information:

- **Basic Info**: Title, price, address, city, state, zip code
- **Property Details**: Bedrooms, bathrooms, square feet, lot size, year built
- **Listing Info**: Agent, agency, listing date, days on market, MLS number
- **Features**: Property features, amenities, description
- **Media**: Images, virtual tour URLs
- **Metadata**: Source URL, website, scrape timestamp

### Sample CSV Output
```csv
title,price,address,bedrooms,bathrooms,square_feet,property_type,source_website
"Beautiful 3BR Home",650000,"123 Main St, San Francisco, CA",3,2.5,1800,"House","Zillow"
```

### Sample JSON Output
```json
{
  "properties": [
    {
      "title": "Beautiful 3BR Home",
      "price": 650000,
      "address": "123 Main St, San Francisco, CA",
      "bedrooms": 3,
      "bathrooms": 2.5,
      "square_feet": 1800,
      "property_type": "House",
      "source_website": "Zillow",
      "scraped_at": "2023-12-01T10:30:00"
    }
  ],
  "total_count": 1,
  "metadata": {
    "scraper_version": "1.0",
    "format": "json"
  }
}
```

## Project Structure

```
Real-Estate-Scraper/
├── main.py                 # Main application entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── config/
│   ├── __init__.py
│   └── settings.py        # Configuration settings
├── src/
│   ├── __init__.py
│   ├── models.py          # Data models
│   ├── base_scraper.py    # Base scraper class
│   └── data_manager.py    # Data storage management
├── scrapers/
│   ├── __init__.py
│   ├── zillow_scraper.py  # Zillow scraper
│   └── realtor_scraper.py # Realtor.com scraper
├── data/                  # Output directory
├── logs/                  # Log files
└── tests/                 # Unit tests (future)
```

## Adding New Scrapers

To add a new real estate website scraper:

1. Create a new file in the `scrapers/` directory
2. Extend the `BaseScraper` class
3. Implement the required abstract methods:
   - `build_search_url()`
   - `scrape_property_list()`
   - `scrape_property_details()`
4. Add the scraper to the main script's `get_available_scrapers()` function

Example:
```python
from src.base_scraper import BaseScraper

class NewSiteScraper(BaseScraper):
    def build_search_url(self, criteria):
        # Implementation here
        pass
    
    def scrape_property_list(self, criteria):
        # Implementation here
        pass
    
    def scrape_property_details(self, property_url):
        # Implementation here
        pass
```

## Best Practices

1. **Respect Rate Limits**: The scraper includes built-in delays and rate limiting
2. **Use Responsibly**: Don't overload target websites with requests
3. **Check robots.txt**: Ensure compliance with website scraping policies
4. **Handle Errors**: The framework includes comprehensive error handling
5. **Monitor Logs**: Check log files for issues and debugging information

## Troubleshooting

### Common Issues

1. **Selenium WebDriver Issues**:
   - Ensure Chrome/Firefox is installed
   - WebDriver will be automatically downloaded on first run

2. **No Properties Found**:
   - Check if the location format is correct
   - Try reducing filters (price range, bedrooms, etc.)
   - Use `--verbose` flag for detailed logging

3. **Permission Errors**:
   - Ensure write permissions for data/ and logs/ directories
   - Run with appropriate user permissions

4. **Network Issues**:
   - Check internet connection
   - Some websites may block automated requests
   - Try adjusting `REQUEST_DELAY` in settings

### Logging

Logs are saved to `logs/scraper.log` and include:
- Info about scraping progress
- Error messages and debugging information
- Performance metrics

Use `--verbose` flag for detailed console output.

## Legal Notice

This tool is for educational and research purposes only. Users are responsible for:
- Complying with website terms of service
- Respecting robots.txt files
- Following applicable laws and regulations
- Using scraped data ethically and legally

Always check the website's terms of service before scraping.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review log files for error details
3. Open an issue on GitHub with detailed information