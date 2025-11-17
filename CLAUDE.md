# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**重要提示**: 请使用中文回答用户的问题和进行交流。

## Project Overview

**ARL (Asset Reconnaissance Lead)** is an asset discovery and reconnaissance tool that helps gather information about target domains and IP addresses. The project uses a microservices architecture with Python as the primary language.

## Architecture

### Technology Stack
- **Backend**: Python 3.12, Flask 3.1
- **Task Queue**: Celery with RabbitMQ
- **Database**: MongoDB 6.x
- **Web Scraping**: Playwright (Chromium + Firefox)
- **Fingerprinting**: wappalyzer-next (full scan mode with Firefox)
- **Scanning Tools**: Nuclei, NPoC framework, massdns, subfinder
- **Containerization**: Docker with Rocky Linux 9

### Core Components

**Services Layer** (`app/services/`):
- `webAnalyze.py`: Web application fingerprinting using wappalyzer-next with Firefox full scan mode
- `siteScreenshot.py`: Website screenshot capture using Playwright + Chromium with resource cleanup
- `portScan.py`: Port scanning service using nmap wrapper
- `massdns.py`: DNS enumeration service
- `nuclei_scan.py`: Vulnerability scanning with Nuclei (auto-updating)
- `infoHunter.py`: WebInfoHunter integration for web information gathering
- `dns_query_plugin/subfinder`: Subdomain discovery using subfinder with configurable API providers

**Tasks Layer** (`app/tasks/`):
- Celery tasks for asynchronous execution
- Separate task types: domain, site, IP, asset, and GitHub monitoring
- Dedicated GitHub worker for repository monitoring

**Routes Layer** (`app/routes/`):
- Flask REST API endpoints with Flask-RESTX
- Token-based authentication
- Namespace-based routing for different resource types

## Development Commands

### Build and Installation
```bash
# Docker installation (recommended)
docker-compose up -d

# Manual installation using setup script
bash misc/setup-arl.sh

# Service management
bash misc/manage.sh start|stop|restart|status|log
```

### Running the Application
```bash
# Install dependencies
pip install -r requirements.txt

# Run Flask application
python app/main.py

# Run Celery worker (main)
celery -A app.celerytask worker --loglevel=info

# Run Celery worker (GitHub-specific)
celery -A app.celerytask worker -Q github --loglevel=info
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest test/test_nuclei_scan.py

# Run with coverage
pytest --cov=app

# Run tests for specific service
pytest test/test_web_analyze.py -v
```

### Database Operations
```bash
# Connect to MongoDB
mongosh mongodb://127.0.0.1:27017/ARLV2

# Export collection data
mongoexport --db ARLV2 --collection asset_domain --out domains.json

# Import collection data
mongoimport --db ARLV2 --collection asset_domain --file domains.json
```

### Task Management
```bash
# List active Celery tasks
celery -A app.celerytask inspect active

# Purge task queue
celery -A app.celerytask purge

# Check task status
celery -A app.celerytask inspect stats
```

### Tool Updates
```bash
# Update Nuclei templates
nuclei -ut

# Update GeoLite2 databases
bash tools/update_geolite2_p3terx.sh

# Update subfinder providers config
# Edit /opt/ARL/app/services/dns_query_plugin/provider-config.yaml
```

## Key Configuration

### Main Configuration Files
- **Config**: `app/config.py` - Main application configuration
- **Runtime Config**: `app/config.yaml` - Runtime settings
- **Subfinder Config**: `app/services/dns_query_plugin/provider-config.yaml` - API provider configuration

### Key Settings
- **MongoDB**: `mongodb://127.0.0.1:27017/ARLV2`
- **RabbitMQ**: `amqp://arl:arlpassword@127.0.0.1:5672/arlv2host`
- **Screenshot Directory**: `app/tmp_screenshot/`
- **Port Scan Ranges**: Configurable TOP_1000, TOP_100, TOP_10 ports

### Environment Variables
- `MAXMIND_LICENSE_KEY`: For GeoLite2 updates from official MaxMind API
- `FOFA_KEY`: FOFA API access key
- `GITHUB_TOKEN`: GitHub API access token
- `PROXY_URL`: HTTP proxy for outbound connections

## Service Architecture Patterns

### Asynchronous Task Processing
- All long-running operations use Celery tasks
- Task status tracking with MongoDB
- Retry mechanisms for failed tasks
- Concurrent execution limits per service type

### Browser Automation
- Playwright with Chromium for screenshots (performance optimized)
- Firefox with wappalyzer-next for fingerprinting (full scan mode)
- Resource cleanup with try-finally patterns
- Multi-threaded screenshot capture

### External Tool Integration
- **Nuclei**: Auto-updating from official projectdiscovery repository
- **Subfinder**: Configurable API providers for subdomain discovery
- **MassDNS**: High-performance DNS resolution
- **GeoLite2**: Automatic database updates from P3TERX repository

### Data Flow
1. API requests trigger Celery tasks
2. Tasks execute external tools or internal services
3. Results stored in MongoDB with proper indexing
4. Real-time status updates via task queues
5. Webhook notifications for completed tasks

## Development Workflow

### Branching Strategy
- `main`: Production-ready code
- Feature branches (e.g., `feature/service-improvement`) for development
- All features merged to main via PR with review

### Code Organization
- Services encapsulate external tool interactions
- Tasks handle asynchronous execution and status management
- Routes provide RESTful API interface
- Helpers contain reusable utility functions
- Modules define data models and enumerations

### Testing Approach
- Unit tests for individual services (`test/test_*.py`)
- Integration tests for external tool interactions
- Mock external dependencies in tests
- Test data in `test/data/` directory when needed

## Security Considerations

- All credential testing tools require explicit authorization context
- Proxy support for anonymized scanning operations
- Rate limiting configurable per service type
- TLS/SSL verification can be disabled for specific reconnaissance tools
- API token-based authentication for all endpoints

## Performance Optimization

- Multi-threaded concurrent processing in services (configurable limits)
- Browser instance reuse with proper cleanup
- Connection pooling for MongoDB operations
- Async task processing with Celery worker scaling
- Resource cleanup after each operation with try-finally patterns

## Troubleshooting

### Common Issues

**Screenshot Service Failures**:
- Check Playwright browsers: `playwright install`
- Verify Chrome/Firefox permissions and dependencies
- Check timeout settings (default 60s)
- Review screenshot directory permissions

**Web Fingerprinting Issues**:
- Ensure Firefox is installed and geckodriver in PATH
- Verify wappalyzer-next dependencies
- Check full scan mode configuration

**Database Connection Issues**:
- MongoDB status: `systemctl status mongod`
- Verify connection string in config.py
- Check database permissions and authentication

**Task Queue Issues**:
- RabbitMQ status: `systemctl status rabbitmq-server`
- Check Celery worker logs: `journalctl -u arl-worker -f`
- Purge failed tasks if needed: `celery -A app.celerytask purge`

**Port Scanning Issues**:
- Verify nmap installation and permissions
- Check if target allows scanning (authorization required)
- Review rate limiting configuration

### Service Logs
```bash
# View service logs
journalctl -u arl-web -f
journalctl -u arl-worker -f
journalctl -u arl-scheduler -f

# View all ARL service logs
journalctl -u 'arl*' -f
```

## External Dependencies

### System Requirements
- Python 3.12+ with virtual environment
- MongoDB 6.x with proper indexing
- RabbitMQ 3.x with management plugin
- Nmap for port scanning operations
- Nuclei (auto-installed via setup script)
- MassDNS for DNS enumeration
- Subfinder for subdomain discovery

### Python Dependencies
- Flask 3.1, Flask-RESTX for API framework
- Celery 5.5.3 for task queue management
- pymongo for MongoDB operations
- Playwright for browser automation
- wappalyzer-next for web fingerprinting
- geoip2 for IP geolocation services

## Recent Architecture Improvements

### v2.6.8 Major Refactoring
1. **PhantomJS Removal**: Replaced with wappalyzer-next + playwright
   - Better performance and reliability
   - Full scan mode for comprehensive fingerprinting
   - Improved resource management with cleanup patterns

2. **Auto-updating External Data**:
   - GeoLite2 databases from P3TERX repository
   - Nuclei from official projectdiscovery repository
   - Automatic updates via GitHub API integration

3. **Subfinder Integration**:
   - Replaced API-based subdomain collection
   - Configurable provider API support
   - Improved subdomain discovery efficiency

4. **Code Quality Improvements**:
   - Removed large binary files (~168MB saved)
   - Optimized .gitignore rules
   - Streamlined setup and deployment process