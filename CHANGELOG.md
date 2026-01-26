# Changelog

All notable changes to this project will be documented in this file.

## [1.4.0] - 2026-01-26

### Added
- Configurable timeout parameter in `AutoskopeApi.__init__()` (default: 20 seconds)
- URL validation for `host` parameter - now requires valid HTTP(S) URLs
- Comprehensive test suite with 29 unit tests using pytest and pytest-asyncio
- Integration tests with real API calls (6 tests, credential-based)
- Secure test runner script `run_integration_tests.py` with hidden password input
- Support for `.env` file for test credentials (via python-dotenv)
- `.env.example` template for integration test credentials
- Enhanced `.gitignore` for better dev environment support
- Test dependencies in `setup.py` extras_require section
- Development documentation in README for running tests
- Export of `CannotConnect` and `InvalidAuth` exceptions in `__init__.py`

### Fixed
- Lazy initialization of `CookieJar` to ensure compatibility with aiohttp 3.13+
  - Previously failed when instantiating `AutoskopeApi` outside an async context
  - Now creates `CookieJar` only when needed (during `connect()`)
- Fixed bare `except:` clause in context manager that could catch system exceptions
- Removed unused variable in `_request()` method (line 116)
- Added debug logging when position data parsing fails
- Fixed README documentation error (`is_parked` → `park_mode`)

### Changed
- Hardcoded timeouts (10s/20s) replaced with configurable `timeout` parameter
- Improved error messages with more context


## [1.3.2] - 2026-01-21

### Fixed
- Exception handling to preserve InvalidAuth type

## [1.3.1] - 2026-01-21

### Added
- CI/CD for PyPI publishing
- py.typed marker for PEP 561 compliance
- Type hints support and licensing

## [1.2.0] - 2025-05-28

### Added
- Internal session management with isolated cookie jars
- Context manager support (`__aenter__`, `__aexit__`) with proper cleanup on failure
- Library now suitable for standalone use

### Changed
- Each API instance now creates and manages its own aiohttp.ClientSession

## [1.1.0] - Initial Release

### Added
- Initial implementation of Autoskope API client
- Basic authentication support
- Vehicle data fetching
- GeoJSON position parsing
- Type hints throughout the codebase

[1.4.0]: https://github.com/mcisk/autoskope_client/compare/v1.3.2...v1.4.0
[1.3.2]: https://github.com/mcisk/autoskope_client/compare/v1.3.1...v1.3.2
[1.3.1]: https://github.com/mcisk/autoskope_client/compare/v1.2.0...v1.3.1
[1.2.0]: https://github.com/mcisk/autoskope_client/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/mcisk/autoskope_client/releases/tag/v1.1.0
