# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Social Media Downloader is a Python CLI tool for downloading videos from various social media platforms (YouTube, TikTok, Instagram, Facebook, X, etc.). It uses yt-dlp and instaloader as backends and provides an interactive command-line interface.

## Development Commands

### Package Management
- `make install` - Install package locally
- `make install-dev` - Install in development mode with dev dependencies
- `make run` - Run the CLI using `social-media-downloader`
- `python -m smd.downloader` - Run the CLI directly from source

### Testing & Code Quality
- `make test` - Run pytest with coverage (tests located in `test/`)
- `python -m pytest test/` - Alternative way to run tests
- `make format` - Format code with Black and lint with flake8
- `black smd/` - Format code only
- `flake8 smd/` - Lint code only
- `mypy smd/` - Type checking (configured in pyproject.toml)
- `isort smd/` - Sort imports

### Building & Distribution
- `make build` - Build Python package using `python -m build`
- `make clean` - Clean build artifacts and cache files
- `make docker-build` - Build Docker image
- `make docker-run` - Run Docker container interactively

## Architecture

### Core Module Structure
- `smd/downloader.py` - Main CLI application with all core functionality
- `smd/__init__.py` - Package initialization and exported functions
- `smd/__main__.py` - Entry point for `python -m smd`

### Key Components in downloader.py
1. **Configuration Management** - JSON config file handling with validation
2. **Network Utilities** - Internet connection checking and retry logic
3. **Download Engines**:
   - YouTube/TikTok/Generic: Uses yt-dlp backend
   - Instagram: Uses instaloader backend for posts/reels
4. **Format Handling** - Interactive format selection with tabulated display
5. **Batch Processing** - Support for .txt files with multiple URLs
6. **History Tracking** - CSV-based download history logging
7. **Update Checking** - PyPI version comparison and update notifications

### Configuration System
- Config stored in `config.json` in working directory
- Supports: default format, download directory, MP3 quality, history file
- Auto-validation and correction of invalid config values
- Default download location: `media/` directory

### Supported Platforms
The tool maintains an `SUPPORTED_DOMAINS` list in `downloader.py` that includes major social media platforms. The actual download capability extends to all yt-dlp supported sites.

## Development Workflow

### Code Standards
- Python 3.10+ required
- Black formatting (88 char line length)
- flake8 linting
- mypy type checking with strict settings
- isort for import sorting

### Testing
- Tests in `test/test.py` using unittest framework
- Comprehensive coverage of config management, URL validation, file operations
- Mock-based testing for external dependencies

### Package Structure
- Entry points: `smd` and `social-media-downloader` commands
- Installable via pip: `pip install social-media-downloader`
- Docker support with volume mounting for downloads

## Dependencies

### Runtime Dependencies
- yt-dlp (video downloading engine)
- instaloader (Instagram-specific downloader)
- requests (HTTP requests)
- tqdm (progress bars)
- ffmpeg-python (video processing)
- pyfiglet, termcolor, tabulate (CLI formatting)

### Development Dependencies
- pytest with coverage
- black, flake8, mypy, isort (code quality)
- pre-commit (git hooks)

## Important Notes

- FFmpeg must be installed on the system for video processing
- Downloads are logged to CSV file for history tracking
- The tool includes update checking against PyPI releases
- Instagram downloads require special handling via instaloader
- Batch downloads supported via text files with one URL per line
- Configuration is automatically created and validated on first run