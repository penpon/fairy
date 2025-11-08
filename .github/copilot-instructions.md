# Copilot Instructions for fairy Repository

## Repository Overview

This is a **Yahoo Auction Scraper** with Rapras authentication - a Python-based web scraping and automation tool that authenticates with Rapras (https://www.rapras.jp/) and Yahoo Auctions (https://auctions.yahoo.co.jp/) to collect seller data. The project uses Playwright for browser automation and supports SMS authentication with proxy server configuration.

**Project Type**: Python 3.12+ application with async/await patterns
**Size**: ~20 Python files, small-to-medium codebase
**Primary Language**: Python 3.12+
**Package Manager**: `uv` (modern Python package manager)
**Runtime**: CPython 3.12.3

## Core Technologies

- **Playwright 1.55.0**: Browser automation and web scraping
- **pytest**: Testing framework with async support (pytest-asyncio)
- **Black**: Code formatting (line length: 100)
- **Ruff**: Fast Python linter and formatter
- **bandit**: Security vulnerability scanner
- **pip-audit**: Dependency vulnerability scanner

## Project Structure

```
/home/runner/work/fairy/fairy/
├── .github/
│   └── workflows/
│       └── tests.yml           # CI/CD pipeline with 3 jobs: test, lint, security
├── modules/
│   ├── config/
│   │   └── settings.py         # Environment variable configuration
│   ├── scraper/
│   │   ├── rapras_scraper.py   # Rapras authentication
│   │   ├── yahoo_scraper.py    # Yahoo Auctions with proxy & SMS
│   │   └── session_manager.py  # Cookie persistence
│   └── utils/
│       └── logger.py           # Logging utility
├── tests/
│   ├── integration/            # E2E tests (require manual SMS input)
│   │   └── test_authentication_flow.py
│   ├── test_config/            # Unit tests for configuration
│   ├── test_scraper/           # Unit tests for scrapers
│   └── test_utils/             # Unit tests for utilities
├── pyproject.toml              # Project dependencies and tool config
├── .env.example                # Example environment variables
└── .gitignore                  # Excludes .venv/, sessions/, .env
```

## Environment Setup

### Required Tools

1. **Python 3.12+**: The project requires Python 3.12 or later
2. **uv**: Modern Python package manager (install with `pip install uv`)
3. **Playwright browsers**: Chromium browser for automation

### Installation Steps (MUST follow this exact order)

```bash
# Step 1: Install uv if not already installed
pip install uv

# Step 2: Create virtual environment
uv venv

# Step 3: Install all dependencies including dev dependencies
uv pip install -e ".[dev]"

# Step 4: Install Playwright browsers (for integration tests only)
# Note: This can fail with download errors, but unit tests will still work
uv run playwright install chromium
```

**Important**: If `playwright install chromium` fails with download errors, you can still run unit tests. Integration tests will be skipped automatically if browsers aren't installed.

### Environment Variables

Copy `.env.example` to `.env` and configure:
- `RAPRAS_USERNAME` and `RAPRAS_PASSWORD`: Rapras credentials
- `YAHOO_PHONE_NUMBER`: Phone number for Yahoo SMS auth (no hyphens, e.g., 09012345678)
- `PROXY_URL`: Proxy server URL (e.g., http://164.70.96.2:3128)
- `PROXY_USERNAME` and `PROXY_PASSWORD`: Proxy BASIC auth credentials

**Note**: The `.env` file is git-ignored and should never be committed.

## Build and Validation Commands

### Code Formatting (ALWAYS run first)

```bash
# Format code with Black (auto-fixes)
uv run black modules/ tests/

# Check formatting with Ruff (must pass)
uv run ruff format --check modules/ tests/
```

**Known Issue**: There's a formatting conflict between Black and Ruff format in `modules/config/settings.py`. If `ruff format --check` fails, run:
```bash
uv run ruff format modules/ tests/
```

### Linting (ALWAYS run after formatting)

```bash
# Check with Ruff linter
uv run ruff check modules/ tests/

# Auto-fix issues (recommended)
uv run ruff check --fix modules/ tests/
```

### Testing

**Unit Tests (fast, ~12 seconds)**:
```bash
# Run all unit tests (excludes integration tests)
uv run pytest tests/ -m "not integration" -v --timeout=300
```

**With Coverage (required, must be ≥80%)**:
```bash
# Run unit tests with coverage report
uv run pytest tests/ -m "not integration" -v --cov=modules --cov-report=xml --cov-report=term-missing --timeout=300

# Check coverage threshold
uv run coverage report --fail-under=80 --format=text
```

**Integration Tests (slow, require manual SMS input)**:
```bash
# Run integration tests only (requires .env setup and SMS codes)
uv run pytest tests/integration/ -m integration -v

# Skip integration tests (default for CI)
uv run pytest tests/ -m "not integration" -v
```

**Important Test Notes**:
- 2 unit tests currently fail (`test_login_failure_invalid_credentials` in rapras_scraper and yahoo_scraper). These are pre-existing issues and should be ignored.
- Integration tests require manual SMS code input within 3 minutes
- Integration tests are automatically skipped in CI/CD
- Current unit test coverage: ~73% (below 80% threshold, but existing state)

### Security Checks

```bash
# Install security tools (if not already installed)
uv pip install bandit pip-audit

# Run bandit security scan (checks for code vulnerabilities)
uv run bandit -r modules/ tests/ -ll -f txt

# Run pip-audit (checks for dependency vulnerabilities)
# Note: This has a 60-second timeout in CI
timeout 60 uv run pip-audit
```

### Complete Validation Pipeline (Run before committing)

**Execute in this exact order**:

```bash
# 1. Format code
uv run black modules/ tests/
uv run ruff format modules/ tests/

# 2. Lint code
uv run ruff check --fix modules/ tests/

# 3. Run unit tests with coverage
uv run pytest tests/ -m "not integration" -v --cov=modules --cov-report=xml --cov-report=term-missing --timeout=300 --tb=short

# 4. Verify coverage threshold
uv run coverage report --fail-under=80 --format=text

# 5. Security checks
uv run bandit -r modules/ tests/ -ll -f txt
timeout 60 uv run pip-audit
```

## GitHub Actions CI/CD

The repository has 3 CI jobs in `.github/workflows/tests.yml`:

1. **test**: Runs unit tests and coverage (must be ≥80%)
2. **lint**: Runs Black and Ruff format/lint checks
3. **security**: Runs bandit and pip-audit

All jobs use:
- Python 3.12
- `uv` for dependency management
- Caching for `.venv` directory

**Important**: The CI skips integration tests automatically using `-m "not integration"`.

## Common Issues and Workarounds

### 1. Playwright Browser Installation Fails

**Symptom**: `playwright install chromium` fails with "Download failed: size mismatch"

**Solution**: This is a known intermittent issue. Unit tests will still work. Integration tests will be skipped automatically.

### 2. Ruff Format vs Black Conflict

**Symptom**: `ruff format --check` fails even after running `black`

**Solution**: Run `uv run ruff format modules/ tests/` to apply Ruff's formatting. The issue is in `modules/config/settings.py` where string concatenation formatting differs.

### 3. Test Failures in Login Tests

**Symptom**: 2 tests fail: `test_login_failure_invalid_credentials` in both scrapers

**Solution**: These are pre-existing test issues (tests expect LoginError but it's not raised). Ignore these failures or fix the scraper implementations to raise LoginError after max retries.

### 4. Coverage Below 80%

**Symptom**: Coverage is ~73% (below 80% threshold)

**Solution**: This is the current state. When adding new code, ensure your changes increase or maintain coverage. The scrapers have low coverage due to untested error paths.

### 5. pip-audit Timeout

**Symptom**: pip-audit hangs or takes too long

**Solution**: Use timeout: `timeout 60 uv run pip-audit` (60 seconds as configured in CI)

## Key Architectural Details

### Authentication Flow
1. **Rapras Login**: Username/password auth → saves session cookies
2. **Yahoo Auctions Login**: Phone number → SMS code (manual input) → proxy authentication
3. **Session Restoration**: Reuses saved cookies to skip login

### Session Management
- Sessions stored in `sessions/` directory (git-ignored)
- Format: `{service_name}_session.json` (e.g., `rapras_session.json`)
- Managed by `SessionManager` class

### Async/Await Patterns
- All scraper operations use `async/await`
- Tests use `pytest-asyncio` with `asyncio_mode = "auto"`
- Playwright operations are fully async

### Logging
- Custom logger in `modules/utils/logger.py`
- Format: `YYYY-MM-DD HH:MM:SS - module.name - LEVEL - message`
- Sensitive data (passwords, phone numbers) not logged

## Development Workflow

1. **Make Changes**: Edit code in `modules/` or `tests/`
2. **Format**: Run `black` and `ruff format`
3. **Lint**: Run `ruff check --fix`
4. **Test**: Run unit tests with coverage
5. **Security**: Run bandit and pip-audit
6. **Commit**: Commit changes if all checks pass

## Quality Requirements

- ✅ **All linting checks must pass** (Black, Ruff)
- ✅ **All unit tests must pass** (except 2 known failures)
- ⚠️ **Coverage should be ≥80%** (currently 73%, maintain or improve)
- ✅ **No security vulnerabilities** (bandit and pip-audit clean)
- ❌ **Never delete tests** to artificially improve coverage
- ❌ **Never commit .env file** (use .env.example)

## Time Estimates

- **Dependency installation**: 30-60 seconds
- **Unit tests**: ~12 seconds
- **Linting (black + ruff)**: ~2 seconds
- **Security scans**: ~5-10 seconds
- **Playwright browser install**: 2-5 minutes (if successful)

## Trust These Instructions

These instructions have been validated by running all commands in a clean environment. If you encounter issues not documented here, verify:
1. Python version is 3.12+
2. `uv` is installed
3. Virtual environment is activated (`.venv/`)
4. All dependencies are installed with `uv pip install -e ".[dev]"`

Only search the codebase if these instructions are incomplete or incorrect.
