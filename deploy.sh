#!/bin/bash
# Real Estate Scraper - Deployment Script
# Automated setup and deployment for production environments

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="real-estate-scraper"
PYTHON_VERSION="3.8"
REQUIRED_SPACE_GB=2

echo -e "${BLUE}🏠 Real Estate Scraper - Deployment Script${NC}"
echo "=================================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}❌ This script should not be run as root${NC}"
   exit 1
fi

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check system requirements
check_requirements() {
    print_info "Checking system requirements..."
    
    # Check Python version
    if command -v python3 &> /dev/null; then
        PYTHON_VER=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        print_status "Python $PYTHON_VER found"
    else
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check pip
    if command -v pip3 &> /dev/null; then
        print_status "pip3 found"
    else
        print_error "pip3 is required but not installed"
        exit 1
    fi
    
    # Check available disk space
    AVAILABLE_SPACE=$(df . | awk 'NR==2 {print $4}')
    AVAILABLE_GB=$((AVAILABLE_SPACE / 1024 / 1024))
    
    if [ $AVAILABLE_GB -lt $REQUIRED_SPACE_GB ]; then
        print_error "Insufficient disk space. Required: ${REQUIRED_SPACE_GB}GB, Available: ${AVAILABLE_GB}GB"
        exit 1
    else
        print_status "Sufficient disk space available (${AVAILABLE_GB}GB)"
    fi
    
    # Check for git
    if command -v git &> /dev/null; then
        print_status "Git found"
    else
        print_warning "Git not found - manual deployment only"
    fi
}

# Setup virtual environment
setup_venv() {
    print_info "Setting up virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_status "Virtual environment created"
    else
        print_status "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    print_status "Virtual environment activated"
    
    # Upgrade pip
    pip install --upgrade pip
    print_status "pip upgraded"
}

# Install dependencies
install_dependencies() {
    print_info "Installing Python dependencies..."
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_status "Dependencies installed from requirements.txt"
    else
        print_warning "requirements.txt not found, installing core dependencies"
        pip install requests beautifulsoup4 selenium pandas lxml python-dotenv sqlalchemy fake-useragent webdriver-manager aiohttp flask gunicorn schedule
    fi
    
    # Install system dependencies for web browsers
    print_info "Checking browser dependencies..."
    
    if command -v google-chrome &> /dev/null || command -v chromium &> /dev/null; then
        print_status "Chrome/Chromium found"
    else
        print_warning "Chrome/Chromium not found - Selenium may not work properly"
        print_info "To install Chrome: wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -"
        print_info "sudo sh -c 'echo \"deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main\" >> /etc/apt/sources.list.d/google-chrome.list'"
        print_info "sudo apt update && sudo apt install google-chrome-stable"
    fi
}

# Setup directories
setup_directories() {
    print_info "Setting up project directories..."
    
    # Create necessary directories
    mkdir -p data logs cache config static templates
    
    # Set permissions
    chmod 755 data logs cache
    chmod 644 config/* 2>/dev/null || true
    
    print_status "Directories created and configured"
}

# Setup configuration files
setup_config() {
    print_info "Setting up configuration files..."
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_status "Created .env from .env.example"
        else
            cat > .env << EOF
# Real Estate Scraper Configuration
DATABASE_URL=sqlite:///data/properties.db
LOG_LEVEL=INFO
CACHE_EXPIRY_HOURS=24
MAX_CONCURRENT_REQUESTS=5
REQUEST_DELAY=2
EOF
            print_status "Created default .env file"
        fi
    else
        print_status ".env file already exists"
    fi
    
    # Create scheduled jobs config if it doesn't exist
    if [ ! -f "config/scheduled_jobs.json" ]; then
        mkdir -p config
        print_status "Configuration directory ready"
    fi
}

# Setup systemd service (Linux only)
setup_service() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        print_info "Setting up systemd service..."
        
        # Create service file
        SERVICE_FILE="$HOME/.config/systemd/user/${PROJECT_NAME}.service"
        mkdir -p "$HOME/.config/systemd/user"
        
        cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Real Estate Scraper
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
EOF
        
        # Enable and start service
        systemctl --user daemon-reload
        systemctl --user enable "${PROJECT_NAME}.service"
        
        print_status "Systemd service created (use 'systemctl --user start ${PROJECT_NAME}' to start)"
    else
        print_warning "Systemd service setup skipped (not on Linux)"
    fi
}

# Test installation
test_installation() {
    print_info "Testing installation..."
    
    # Test basic functionality
    if python3 test_scraper.py > /dev/null 2>&1; then
        print_status "Basic functionality test passed"
    else
        print_warning "Basic functionality test failed - check dependencies"
    fi
    
    # Test async functionality
    if python3 async_test.py > /dev/null 2>&1; then
        print_status "Async functionality test passed"
    else
        print_warning "Async functionality test failed - may need additional dependencies"
    fi
    
    # Test scheduler
    if python3 scheduler.py --demo > /dev/null 2>&1; then
        print_status "Scheduler test passed"
    else
        print_warning "Scheduler test failed"
    fi
    
    # Test web dashboard
    if timeout 5 python3 web_dashboard.py > /dev/null 2>&1; then
        print_status "Web dashboard test passed"
    else
        print_warning "Web dashboard test failed"
    fi
}

# Setup Docker environment
setup_docker() {
    if command -v docker &> /dev/null; then
        print_info "Setting up Docker environment..."
        
        # Build Docker image
        if [ -f "Dockerfile" ]; then
            docker build -t "${PROJECT_NAME}:latest" .
            print_status "Docker image built"
            
            # Create docker-compose override for local development
            if [ -f "docker-compose.yml" ]; then
                print_status "Docker Compose ready for deployment"
                print_info "Use 'docker-compose up -d' to start all services"
            fi
        else
            print_warning "Dockerfile not found - Docker setup skipped"
        fi
    else
        print_warning "Docker not found - container setup skipped"
    fi
}

# Generate deployment report
generate_report() {
    print_info "Generating deployment report..."
    
    REPORT_FILE="deployment_report_$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$REPORT_FILE" << EOF
Real Estate Scraper - Deployment Report
Generated: $(date)
========================================

System Information:
- OS: $(uname -s) $(uname -r)
- Python: $(python3 --version)
- Working Directory: $(pwd)
- User: $(whoami)

Project Structure:
$(find . -maxdepth 2 -type f -name "*.py" | head -20)

Configuration:
- Environment file: $([[ -f ".env" ]] && echo "✅ Present" || echo "❌ Missing")
- Virtual environment: $([[ -d "venv" ]] && echo "✅ Present" || echo "❌ Missing")
- Data directory: $([[ -d "data" ]] && echo "✅ Present" || echo "❌ Missing")
- Logs directory: $([[ -d "logs" ]] && echo "✅ Present" || echo "❌ Missing")

Next Steps:
1. Review configuration in .env file
2. Test scraping: python main.py "Austin, TX" --max-pages 1
3. Start scheduler: python scheduler.py
4. Access dashboard: python web_dashboard.py (then visit http://localhost:5000)
5. For production: Use Docker Compose or systemd service

Commands:
- Basic scraping: python main.py "City, State"
- Async scraping: python async_test.py
- Start scheduler: python scheduler.py
- Web dashboard: python web_dashboard.py
- CLI utilities: python utils/scraper_cli.py --help

EOF
    
    print_status "Deployment report saved to $REPORT_FILE"
}

# Main deployment function
main() {
    echo -e "${BLUE}Starting deployment process...${NC}"
    echo
    
    # Run deployment steps
    check_requirements
    setup_venv
    install_dependencies
    setup_directories
    setup_config
    setup_service
    test_installation
    setup_docker
    generate_report
    
    echo
    echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
    echo
    print_info "Quick Start Commands:"
    echo "  1. Test basic functionality: python test_scraper.py"
    echo "  2. Run a quick scrape: python main.py 'Austin, TX' --max-pages 1"
    echo "  3. Start web dashboard: python web_dashboard.py"
    echo "  4. View system status: python utils/scraper_cli.py setup check"
    echo
    print_info "For production deployment:"
    echo "  • Docker: docker-compose up -d"
    echo "  • Systemd: systemctl --user start ${PROJECT_NAME}"
    echo
    print_warning "Don't forget to:"
    echo "  • Review and customize the .env configuration file"
    echo "  • Configure scheduled jobs in config/scheduled_jobs.json"
    echo "  • Set up appropriate rate limiting for target websites"
    echo "  • Ensure compliance with website terms of service"
}

# Handle command line arguments
case "${1:-}" in
    "test")
        print_info "Running test deployment..."
        check_requirements
        test_installation
        ;;
    "docker")
        print_info "Running Docker-only setup..."
        setup_docker
        ;;
    "clean")
        print_info "Cleaning deployment artifacts..."
        rm -rf venv __pycache__ .pytest_cache
        find . -name "*.pyc" -delete
        print_status "Cleanup completed"
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [command]"
        echo "Commands:"
        echo "  (none)  - Full deployment"
        echo "  test    - Test existing installation"
        echo "  docker  - Setup Docker environment only"
        echo "  clean   - Clean deployment artifacts"
        echo "  help    - Show this help"
        ;;
    *)
        main
        ;;
esac