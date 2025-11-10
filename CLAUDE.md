# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ARL (Asset Reconnaissance Lead)** is an asset discovery and reconnaissance tool that helps gather information about target domains and IP addresses. The project uses a microservices architecture with Python as the primary language.

## Architecture

### Technology Stack
- **Backend**: Python 3.12, Flask 3.1
- **Task Queue**: Celery with RabbitMQ
- **Database**: MongoDB
- **Web Scraping**: Playwright (Chromium + Firefox)
- **Fingerprinting**: wappalyzer-next (full scan mode with Firefox)
- **Scanning Tools**: Nuclei, NPoC framework, massdns
- **Containerization**: Docker

### Core Components

**Services Layer** (`app/services/`):
- `webAnalyze.py`: Web application fingerprinting using wappalyzer-next
- `siteScreenshot.py`: Website screenshot capture using Playwright + Chromium
- `portScan.py`: Port scanning service
- `massdns.py`: DNS enumeration
- `commonTask.py`: Common task operations
- `nuclei_scan.py`: Vulnerability scanning with Nuclei
- `infoHunter.py`: WebInfoHunter integration

**Tasks Layer** (`app/tasks/`):
- Celery tasks for asynchronous execution
- Domain tasks, site tasks, IP tasks

**Routes Layer** (`app/routes/`):
- Flask REST API endpoints
- Domain, asset, and task management routes

## Development Setup

### Prerequisites
- Python 3.12
- Docker & Docker Compose
- MongoDB
- RabbitMQ

### Installation

**Option 1: Using setup script**
```bash
bash misc/setup-arl.sh
```

**Option 2: Manual Docker build**
```bash
cd docker/worker
docker build -t arl-worker .
# Build other services (frontend, etc.)
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start services
docker-compose up -d  # or use setup-arl.sh

# Run ARL application
python app/main.py

# Run Celery worker
celery -A app.celerytask worker --loglevel=info
```

## Key Services

### Web Analysis Service
- **File**: `app/services/webAnalyze.py`
- **Technology**: wappalyzer-next with Firefox (full scan mode)
- **Usage**: Detects web technologies, frameworks, CMS, JavaScript libraries
- **Note**: Uses full scan mode for better detection accuracy

### Screenshot Service
- **File**: `app/services/siteScreenshot.py`
- **Technology**: Playwright with Chromium
- **Resource Management**: Uses try-finally to ensure proper cleanup
- **Concurrency**: Multi-threaded screenshot capture

### Port Scanning
- **File**: `app/services/portScan.py`
- **Technology**: nmap wrapper
- **Approach**: Scans common ports and services

### Nuclei Vulnerability Scanner
- **Auto-updating**: setup-arl.sh fetches latest version from official repo
- **Template Management**: Updates automatically with `nuclei -ut`
- **Location**: `/usr/bin/nuclei`

## Database Updates

### GeoLite2 Databases
- **Source**: P3TERX/GeoLite.mmdb (https://github.com/P3TERX/GeoLite.mmdb)
- **Auto-download**: Implemented in setup-arl.sh
- **API**: Uses GitHub API to get latest release tag
- **Files**:
  - GeoLite2-ASN.mmdb (IP to ASN mapping)
  - GeoLite2-City.mmdb (IP to location mapping)
- **Location**: `/data/GeoLite2/`

## Common Commands

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest test/test_nuclei_scan.py

# Run with coverage
pytest --cov=app
```

### Database Operations
```bash
# Connect to MongoDB
mongosh mongodb://127.0.0.1:27017/ARLV2

# Export data
mongoexport --db ARLV2 --collection asset_domain --out domains.json
```

### Task Management
```bash
# List Celery tasks
celery -A app.celerytask inspect active

# Purge task queue
celery -A app.celerytask purge
```

### Tool Updates
```bash
# Update Nuclei templates
nuclei -ut

# Update GeoLite2 databases
bash tools/update_geolite2_p3terx.sh
```

## Configuration

### Main Config
- **File**: `app/config.py`
- **Runtime Config**: `app/config.yaml`

Key settings:
- MongoDB connection
- Celery broker URL
- Concurrent settings
- Proxy configurations

### Environment Variables
- `MAXMIND_LICENSE_KEY`: For GeoLite2 updates from official MaxMind API
- `FOFA_KEY`: FOFA API access
- `GITHUB_TOKEN`: GitHub API access
- `PROXY_URL`: HTTP proxy for outbound connections

## Recent Changes

### Major Refactoring (v2.6.8)
1. **PhantomJS Removal**: Replaced with wappalyzer + playwright
   - Better performance and reliability
   - Full scan mode for fingerprinting
   - Resource management improvements

2. **Auto-updating External Data**:
   - GeoLite2 databases from P3TERX
   - Nuclei from official projectdiscovery repo
   - Automatic via GitHub API

3. **Code Cleanup**:
   - Removed large binary files (~168MB saved)
   - Optimized .gitignore rules
   - Streamlined setup process

## Development Workflow

### Branching Strategy
- `main`: Production-ready code
- Feature branches (e.g., `2.6.8`) for development
- All features merged to main via PR

### Making Changes
1. Create feature branch from main
2. Make changes with tests
3. Test locally with Docker
4. Submit PR for review
5. Merge to main
6. Delete feature branch

### Testing Approach
- Unit tests in `test/` directory
- Integration tests for services
- Manual testing for UI components
- Docker-based testing for full stack

## Troubleshooting

### Common Issues

**Screenshot failures**:
- Check Playwright browsers installed
- Verify Chrome/Firefox permissions
- Check timeout settings (60s default)

**Fingerprinting issues**:
- Ensure Firefox is installed
- Verify geckodriver in PATH
- Check wappalyzer dependencies

**Database connection**:
- MongoDB running: `systemctl status mongod`
- Check connection string in config
- Verify database permissions

**Task queue issues**:
- RabbitMQ status: `systemctl status rabbitmq-server`
- Check Celery worker logs
- Purge failed tasks if needed

## Dependencies

### Python Packages (requirements.txt)
- Flask, Flask-RESTX for API
- Celery for task queue
- pymongo for MongoDB
- Playwright for browser automation
- wappalyzer for fingerprinting
- geoip2 for IP geolocation
- Various scanning and analysis tools

### System Dependencies
- nmap for port scanning
- massdns for DNS enumeration
- Nuclei for vulnerability scanning
- NPoC framework for exploitation

## Security Considerations

- All credential testing tools require explicit authorization
- Supports proxy configuration for anonymized scanning
- Rate limiting configurable per service
- TLS/SSL verification can be disabled for specific tools

## Performance Optimization

- Multi-threaded concurrent processing in services
- Browser instance reuse (Playwright)
- Connection pooling for database
- Async task processing with Celery
- Resource cleanup after each operation

## Additional Resources

- Documentation: Project README and inline comments
- API Docs: Flask-RESTX automatically generated
- Monitoring: Logs in /var/log/arl/ (when deployed)
- Tools: Various third-party tools in /opt/ARL-NPoC/
