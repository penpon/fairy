# Copilot Code Review Instructions

**Role**: You are a code reviewer for the Yahoo Auction Scraper project. Focus on architecture compliance, quality standards, and security risks within the Phase 1-2 implementation scope.

---

## 📋 Review Priority (High → Low)

### 🔴 **Critical: Issues requiring immediate attention**

1. **Security Risks**
   - [ ] `.env` file committed (strictly prohibited)
   - [ ] Hardcoded credentials (RAPRAS_USERNAME, RAPRAS_PASSWORD, PROXY_PASSWORD, etc.)
   - [ ] Logging passwords or phone numbers
   - [ ] bandit High severity warnings
   - [ ] Dependency vulnerabilities detected by pip-audit

2. **Architecture Violations**
   - [ ] Module boundary violations (reversing Scraper → Analyzer → Storage order)
   - [ ] Missing dependency injection (directly referencing external dependencies instead of constructor injection)
   - [ ] Relative imports (`from .module import`)
   - [ ] Wildcard imports (`from module import *`)

3. **Data Quality & Performance**
   - [ ] **Data extraction accuracy**: Implementation that cannot achieve 100%
   - [ ] **Connection success rate**: Missing retry implementation or less than 3 retries
   - [ ] **Processing speed**: Risk of exceeding 30 seconds per seller (synchronous processing, heavy loops, etc.)

### 🟡 **High: Important but fixable**

4. **Code Quality Standards**
   - [ ] Black format violations (line length > 100)
   - [ ] Ruff linter errors (unused imports, variables, etc.)
   - [ ] Missing type hints (type hints required for all functions)
   - [ ] Missing docstrings (Google Style: Args, Returns, Raises)

5. **Test Requirements**
   - [ ] Insufficient tests for new implementations
   - [ ] **Test deletion** (deleting tests to maintain coverage is strictly prohibited)
   - [ ] Missing test design matrix (see structure.md)
   - [ ] Missing Given/When/Then comments
   - [ ] Insufficient error case tests (normal cases ≥ error cases is a violation)
   - [ ] Missing exception validation (validate exception type and message with pytest.raises)
   - [ ] Coverage below 80% (require additional tests)

6. **Code Size & Complexity**
   - [ ] Files exceeding 500 lines
   - [ ] Functions exceeding 50 lines
   - [ ] Nesting depth of 4 or more levels
   - [ ] Classes with more than 15 methods

### 🟢 **Medium: Recommended improvements**

7. **Naming Conventions**
   - [ ] Class names not in PascalCase
   - [ ] Functions/variables not in snake_case
   - [ ] Constants not in UPPER_SNAKE_CASE
   - [ ] Private methods not in `_snake_case`

8. **Error Handling**
   - [ ] Exception swallowing (`except: pass`)
   - [ ] Not using appropriate exception types (generic Exception)
   - [ ] Missing exponential backoff (during retries)

9. **Async Patterns**
   - [ ] Inappropriate use of `async/await`
   - [ ] Synchronous execution of Playwright operations
   - [ ] Misuse of `asyncio.run()`

---

## 🎯 Phase 1-2 Scope Verification

### ✅ Implementation Targets (Review Required)
- `modules/scraper/`: Rapras/Yahoo authentication, seller information retrieval
- `modules/analyzer/`: Product data analysis, anime filtering (using `gemini -p` command)
- `modules/storage/`: CSV export, data models
- `modules/config/`: Environment variable management
- `modules/utils/`: Logging configuration

### ❌ Out of Scope (Phase 3+)
- Web frontend (React)
- Backend API (FastAPI)
- Database integration
- AI chat functionality
- CRM system

Flag code containing Phase 3+ features as "out of scope".

---

## 🔍 Code Review Checklist

### Security
```python
# ❌ Bad Example
password = "mypassword123"  # Hardcoding prohibited
logger.info(f"Login with {phone_number}")  # Phone number logging prohibited

# ✅ Good Example
password = os.getenv("RAPRAS_PASSWORD")
logger.info("Login attempt started")
```

### Architecture
```python
# ❌ Bad Example: Analyzer directly calls Scraper
class ProductAnalyzer:
    def analyze(self):
        scraper = RaprasScraper()  # Should use dependency injection
        data = scraper.fetch()

# ✅ Good Example: Constructor injection
class ProductAnalyzer:
    def __init__(self, scraper: RaprasScraper):
        self.scraper = scraper

    def analyze(self, data: list[dict]):
        # Process received data
```

### Imports
```python
# ❌ Bad Example
from .rapras_scraper import RaprasScraper  # Relative imports prohibited
from modules.scraper import *  # Wildcard imports prohibited

# ✅ Good Example
from modules.scraper.rapras_scraper import RaprasScraper
```

### Test Design
```python
# ❌ Bad Example: No Given/When/Then, only normal cases
def test_login():
    scraper.login("valid_user", "valid_pass")
    assert scraper.is_logged_in()

# ✅ Good Example: Structured error case test
def test_login_failure_invalid_credentials():
    """T004: Error case - Login fails with invalid credentials"""
    # Given: Invalid credentials are provided
    scraper = RaprasScraper()

    # When: Attempting to login
    with pytest.raises(LoginError) as exc_info:
        scraper.login("invalid_user", "wrong_pass")

    # Then: LoginError is raised with appropriate message
    assert "Invalid credentials" in str(exc_info.value)
```

### Error Handling
```python
# ❌ Bad Example: Exception swallowing
try:
    result = scraper.fetch()
except:
    pass  # Ignoring errors

# ✅ Good Example: Proper retry and exception handling
@retry(max_attempts=3, backoff_factor=2)
async def fetch_with_retry():
    try:
        return await scraper.fetch()
    except ConnectionError as e:
        logger.error(f"Connection failed: {e}")
        raise
```

### Performance
```python
# ❌ Bad Example: Synchronous processing risks exceeding 30 seconds
def fetch_all_sellers(seller_ids):
    results = []
    for seller_id in seller_ids:
        results.append(fetch_seller(seller_id))  # Sequential processing
    return results

# ✅ Good Example: Async concurrent processing
async def fetch_all_sellers(seller_ids):
    tasks = [fetch_seller(seller_id) for seller_id in seller_ids]
    return await asyncio.gather(*tasks)
```

---

## 📝 Review Comment Format

### Critical (Immediate fix required)
```
🔴 **Critical - Security Risk**
A `.env` file has been committed. This file contains authentication credentials and must be removed immediately.

How to fix:
1. `git rm --cached .env`
2. Verify `.env` is in `.gitignore`
3. Remove from GitHub history as well (`git filter-repo`)
```

### High (Important fix)
```
🟡 **High - Test Coverage**
No tests found for the newly added `ProductAnalyzer.analyze_trends()` method.

Required tests:
- Normal case: Returns statistics for valid product list
- Error cases: Empty list, None, invalid types raise errors
- Boundary values: 0, 1, 1000 data items

Reference: structure.md "Test Case Design Process"
```

### Medium (Recommended improvement)
```
🟢 **Medium - Naming Convention**
Function name `fetchProducts` is in camelCase. Project convention uses snake_case.

Fix example: `fetch_products`
```

---

## 🚫 Out of Review Scope

Do not flag the following (known issues/constraints):

1. **2 existing failing tests**
   - `test_login_failure_invalid_credentials` (rapras_scraper, yahoo_scraper)
   - These are known issues existing before PR creation

2. **73% coverage in existing code**
   - New code must be 80%+, but don't flag existing code coverage issues

3. **Playwright browser install failures**
   - Browser installation for integration tests is environment-dependent

4. **Black vs Ruff format conflicts**
   - Known issue in `modules/config/settings.py`, resolved with Ruff format

---

## 📚 Reference Documentation

Refer to these during review:

- **product.md**: Project overview, Phase 1-2 scope, success criteria
- **structure.md**: Architecture, naming conventions, test design process
- **tech.md**: Technology stack, 7-step quality checks, performance requirements

---

## ✅ Good Review Example

```markdown
## Review Summary

### 🔴 Critical Issues (2)
1. **Security**: Line 45 - Password is hardcoded
2. **Architecture**: Line 78 - `Analyzer` directly depends on `Scraper`

### 🟡 High Priority (3)
1. **Test Coverage**: Missing tests for `analyze_trends()` method
2. **Type Hints**: Functions on lines 23-34 lack type hints
3. **Error Handling**: Exception swallowed on line 56

### 🟢 Improvements (1)
1. **Naming**: Recommend changing function name `fetchData` → `fetch_data`

### ✅ Good Points
- Async processing is properly implemented
- Docstrings are well written
- Error logging is appropriate

---

**Overall**: Please re-review after fixing Critical issues.
```

---

## 🎓 Summary

**Review Focus**:
1. Security (prevent credential leaks)
2. Architecture compliance (dependencies, module separation)
3. Test quality (80% coverage, error cases ≥ normal cases)
4. Performance (30 seconds per seller, 100% data extraction)

**Issue Levels**:
- 🔴 Critical: Immediate fix required (security, architecture violations)
- 🟡 High: Important (insufficient tests, quality standards not met)
- 🟢 Medium: Recommended improvements (naming conventions, refactoring)

**Review Approach**:
- Constructive and specific feedback
- Provide fix examples
- Don't flag known issues
- Strictly adhere to Phase 1-2 scope
