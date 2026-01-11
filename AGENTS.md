# AGENTS.md

Instructions for AI coding agents working on this codebase.

## Build & Run Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run Flask application
python app/main.py

# Run Celery worker (main)
celery -A app.celerytask worker --loglevel=info

# Run Celery worker (GitHub-specific queue)
celery -A app.celerytask worker -Q github --loglevel=info
```

## Testing Commands

```bash
# Run all tests
pytest

# Run single test file
pytest test/test_nuclei_scan.py

# Run single test function
pytest test/test_nuclei_scan.py::test_nuclei_scan_returns_empty_without_binary

# Run tests with verbose output
pytest -v

# Run tests with coverage
pytest --cov=app

# Run tests matching keyword
pytest -k "fingerprint"
```

## Code Style Guidelines

### Import Order
1. Standard library imports
2. Third-party imports
3. Local application imports (from app.*)
4. Late imports at module end use `# noqa: E402` comment

```python
# Standard library
import os
import re
import json

# Third-party
from flask_restx import Namespace, fields
from bson import ObjectId

# Local
from app import utils
from app.config import Config
from app.modules import ErrorMsg
```

### Naming Conventions
- **Files**: camelCase for route files (`assetDomain.py`), snake_case for services (`nuclei_scan.py`)
- **Classes**: PascalCase (`NucleiScan`, `WebAnalyze`, `ARLResource`)
- **Functions/Methods**: snake_case (`check_have_nuclei`, `build_data`)
- **Constants**: UPPER_SNAKE_CASE (`TOP_1000`, `MONGO_URL`)
- **Module variables**: snake_case (`logger`, `error_map`)

### Type Annotations
Use type hints for function signatures:
```python
def check_have_nuclei(self) -> bool:
def nuclei_scan(targets: list) -> list:
```

### String Formatting
Always use f-strings:
```python
logger.info(f"start WebAnalyze {len(self.targets)}")
logger.warning(f"Result file not found: {self.nuclei_result_path}")
```

### Type Consistency Pattern
Ensure consistent types in data structures (common pattern in this codebase):
```python
{
    "template_id": str(data.get("template-id", "")),      # Always str
    "confidence": str(details.get('confidence', 0)),       # Always str
    "categories": list(details.get('categories', []))      # Always list
}
```

### Logging
Use the centralized logger from utils:
```python
from app import utils
logger = utils.get_logger()

# Log levels
logger.debug("Detailed debugging info")
logger.info("General information")
logger.warning("Warning messages")
logger.exception(e)  # For exception stack traces
```

### Error Handling Pattern
```python
try:
    # operation
except SpecificException as e:
    logger.warning(f"Descriptive message: {e}")
    return []  # or default value
except Exception as e:
    logger.exception(e)
    return default_value
```

### Class Design
Use `__slots__` for performance in frequently instantiated classes:
```python
class NucleiScan:
    __slots__ = ('targets', 'nuclei_target_path', 'nuclei_result_path')
    
    def __init__(self, targets: list):
        self.targets = targets
```

### List Comprehensions (Preferred)
Prefer comprehensions over loops for building lists:
```python
# Good - uses comprehension
valid_targets = [
    str(domain).strip()
    for domain in self.targets
    if domain and isinstance(domain, (str, int))
]

# Avoid - explicit loop
valid_targets = []
for domain in self.targets:
    if domain:
        valid_targets.append(str(domain).strip())
```

### Resource Cleanup Pattern
Always use try-finally for resource cleanup:
```python
def run(self):
    try:
        self.exec_operation()
        results = self.dump_result()
    finally:
        self._delete_file()  # Cleanup always runs
    return results
```

### Flask Route Pattern
```python
from flask_restx import Namespace, fields
from app.utils import auth
from . import ARLResource, get_arl_parser

ns = Namespace('resource_name', description="Description")

@ns.route('/')
class ResourceClass(ARLResource):
    parser = get_arl_parser(search_fields, location='args')
    
    @auth
    @ns.expect(parser)
    def get(self):
        """Docstring for API documentation"""
        args = self.parser.parse_args()
        data = self.build_data(args=args, collection='collection_name')
        return data
```

### API Response Pattern
Use `utils.build_ret()` for consistent API responses:
```python
from app.modules import ErrorMsg

# Success
return utils.build_ret(ErrorMsg.Success, {"data": result})

# Error
return utils.build_ret(ErrorMsg.Error, {"error": str(e)})
```

### Service Class Pattern
Services should inherit from `BaseThread` for concurrent execution:
```python
from .baseThread import BaseThread

class WebAnalyze(BaseThread):
    def __init__(self, sites, concurrency=3):
        super().__init__(sites, concurrency=concurrency)
        self.result_map = {}
    
    def work(self, site):
        """Override: process single item"""
        pass
    
    def run(self):
        self._run()
        return self.result_map
```

## Project Architecture

```
app/
├── config.py          # Configuration (Config class)
├── main.py            # Flask app entry point
├── modules/           # Data models, enums, error codes
├── routes/            # Flask REST API endpoints
├── services/          # External tool integrations
├── tasks/             # Celery async tasks
├── helpers/           # Reusable business logic
└── utils/             # Core utilities (logging, db, etc.)
test/                  # Test files (test_*.py)
```

## Database Access
Use `utils.conn_db()` for MongoDB operations:
```python
from app.utils import conn_db

# Query
data = conn_db('collection').find_one({"field": value})

# Insert
conn_db('collection').insert_one(document)

# Update
conn_db('collection').update_one({"_id": id}, {"$set": updates})
```

## Comments
Chinese comments are acceptable (project is Chinese-oriented):
```python
# 预编译正则表达式模式
DOMAIN_PATTERN = re.compile(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
```

## External Command Execution
Use `utils.exec_system()` for subprocess calls:
```python
from app import utils

utils.exec_system(command, timeout=96*60*60)
output = utils.check_output(command, timeout=timeout)
```

## Configuration
Access via `Config` class from `app/config.py`:
```python
from app.config import Config

tmp_path = Config.TMP_PATH
mongo_url = Config.MONGO_URL
```
