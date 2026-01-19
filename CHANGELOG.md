# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

- Initial release of Anti-Bot Core Framework
- Generic anti-bot utilities for web scraping projects
- Human-like navigation patterns (zoom, drag, scroll)
- Mouse movement simulation with Bézier curves
- Grid sweep algorithm for area scanning
- Mercator projection utilities for geographic coordinates
- Browser fingerprint masking
- Resource blocking optimization
- Async worker pool for concurrent processing
- Response interception framework
- Logging utilities with timestamps

### Changed

- Simplified project structure to single core module
- Removed Korean-specific scraper implementations
- Archived example scripts and benchmarks to separate folder

---

## [1.0.0] - 2026-01-19

### Initial Release

First public release of the Anti-Bot Core Framework.

### Core Components

1. **Geographic Functions**
   - `ll_to_pixel()`: Latitude/longitude to pixel conversion
   - `pixel_to_ll()`: Pixel to latitude/longitude conversion
   - `clamp_coordinates()`: Geographic boundary enforcement

2. **Anti-Bot Navigation**
   - `human_like_recenter()`: Multi-step human-like navigation
   - `drag_to_latlon()`: Smooth map dragging
   - `wheel_to_zoom()`: Gradual zoom control
   - `human_scroll()`: Natural scrolling behavior
   - `random_mouse_movements()`: Idle mouse activity
   - `grid_sweep()`: Strategic area scanning

3. **Browser Management**
   - `launch_browser_desktop()`: Desktop browser with anti-bot settings
   - `launch_browser_mobile()`: Mobile browser configuration
   - `create_worker_pool()`: Concurrent worker tabs
   - `setup_resource_blocking()`: Resource filtering

4. **Utilities**
   - `random_delay()`: Variable timing delays
   - `human_think_time()`: Human-like pauses
   - `click_element_safely()`: Safe element interaction
   - `wait_for_element()`: Element detection
   - `ScraperLogger`: Logging utility class

---

## Compatibility

- Python 3.9+
- Playwright Latest
- Compatible with Windows, macOS, and Linux

---

## Acknowledgments

- Playwright team for browser automation
- Open source community for anti-bot research
