# Changelog

All notable changes to Mentalist will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-11-16

### Breaking Changes

- **Python 3.11+ Required**: Mentalist now requires Python 3.11 or higher. Users on older Python versions should use [v1.0](https://github.com/sc0tfree/mentalist/releases/tag/v1.0).
- Migrated from setuptools to Poetry for package management and dependency management.

### Added

- Poetry support with `pyproject.toml` for modern Python packaging.
- Comprehensive installation documentation in README.md covering Poetry, pip, and development setup.
- Error handling for locale operations with graceful fallbacks.
- CHANGELOG.md to track version history and changes.

### Changed

- Updated Python version check to require 3.11+ with informative error messages.
- Replaced deprecated `inspect.getargspec()` with `inspect.signature()` for Python 3.11+ compatibility.
- Replaced deprecated `locale.format()` with `locale.format_string()` with error handling.
- Updated version to 2.0.0 to reflect breaking changes and major modernization.
- Improved locale handling with try/except blocks to prevent crashes on systems with different locale configurations.
- Updated README.md badges to reflect Python 3.11+ requirement and version 2.0.

### Removed

- `setup.py` - replaced by `pyproject.toml`.
- `MANIFEST.in` - package data now managed via `pyproject.toml`.
- `pytest.ini` - test configuration now in `pyproject.toml`.
- `pytest-runner` dependency - pytest can be run directly.

### Fixed

- Fixed compatibility issues with Python 3.11+ where `inspect.getargspec()` was removed.
- Fixed potential crashes from locale operations on systems without specific locales.
- Improved test configuration to work seamlessly with Poetry.

### Development

- PyInstaller spec file updated with Poetry usage instructions.
- All 22 unit tests passing on Python 3.13.
- Package successfully builds as both wheel and source distribution.

## [1.0] - 2018-XX-XX

Initial release of Mentalist.

- Graphical tool for custom wordlist generation.
- Support for Hashcat and John the Ripper rule output.
- Case mutation, substitution, prepend/append operations.
- Built-in dictionaries and wordlists.
- PyInstaller support for standalone executables.

