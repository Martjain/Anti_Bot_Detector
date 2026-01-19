# Anti-Bot Core Framework

Universal anti-bot detection bypass utilities for web scraping. Implements behavioral mimicry, advanced navigation patterns, and stealth techniques.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-Latest-green.svg)](https://playwright.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Features

### Anti-Bot Technology

- Human-like navigation with multi-step zoom and drag patterns
- Mouse movement simulation with Bézier-curve movements
- Grid sweep algorithm for strategic area scanning
- Browser fingerprint masking (WebDriver property hiding)
- Resource blocking for performance optimization

### Geographic Utilities

- Mercator projection for lat/lon to pixel conversion
- Coordinate clamping to specified geographic bounds
- Grid-based scanning with configurable rings and step sizes

### Performance & Concurrency

- Async architecture built on Python asyncio
- Worker pool for concurrent browser tab management
- Response interception for API data extraction

### Utilities

- Human-like delays with random timing
- Safe element interaction with timeout protection
- Built-in logging with timestamps and levels

---

## Installation

```bash
pip install playwright
playwright install chromium
```

---

## Quick Start

```python
import asyncio
from anti_bot_core import (
    launch_browser_desktop,
    human_like_recenter,
    human_think_time,
    setup_resource_blocking,
    ScraperLogger,
)

async def scrape_example():
    logger = ScraperLogger("Example")
    browser, ctx, page = await launch_browser_desktop(headless=False)

    try:
        await setup_resource_blocking(ctx)
        await page.goto("https://example.com")
        await human_think_time(1.0, 2.0)
        logger.success(f"Page title: {await page.title()}")
    finally:
        await ctx.close()
        await browser.close()

asyncio.run(scrape_example())
```

---

## Core Modules

### Navigation

```python
from anti_bot_core import (
    human_like_recenter,
    drag_to_latlon,
    wheel_to_zoom,
    human_scroll,
    grid_sweep,
)

# Human-like navigation to coordinates
await human_like_recenter(page, lat=37.5, lon=126.9, zoom=15)

# Grid-based area scanning
await grid_sweep(
    page,
    center_lat=37.5,
    center_lon=126.9,
    zoom=15,
    rings=2,
    step_px=500,
    dwell_s=0.5,
)
```

### Browser Management

```python
from anti_bot_core import (
    launch_browser_desktop,
    launch_browser_mobile,
    create_worker_pool,
    setup_resource_blocking,
)

# Desktop browser
browser, ctx, page = await launch_browser_desktop(
    headless=False,
    viewport_width=1920,
    viewport_height=1080,
)

# Mobile browser
browser, ctx, page = await launch_browser_mobile(
    device_name="iPhone 14 Pro Max",
    headless=False,
)

# Worker pool for concurrent operations
worker_pool = await create_worker_pool(ctx, worker_count=12)
```

### Utilities

```python
from anti_bot_core import (
    random_delay,
    human_think_time,
    click_element_safely,
    wait_for_element,
    ScraperLogger,
)

# Random delay between operations
await asyncio.sleep(random_delay(0.5, 2.0))

# Human-like thinking time
await human_think_time(1.0, 3.0)

# Safe element interaction
await click_element_safely(page, ".submit-button")
await wait_for_element(page, "#results")

# Logging
logger = ScraperLogger("MyScraper")
logger.info("Processing started")
logger.success("Task completed")
```

---

## API Reference

### Geographic Functions

| Function | Description |
|----------|-------------|
| `ll_to_pixel(lat, lon, z)` | Convert lat/lon to pixel coordinates |
| `pixel_to_ll(x, y, z)` | Convert pixel coordinates to lat/lon |
| `clamp_coordinates(lat, lon, bounds)` | Constrain coordinates to bounds |

### Navigation Functions

| Function | Description |
|----------|-------------|
| `human_like_recenter(page, lat, lon, zoom)` | Human-like navigation to coordinates |
| `drag_to_latlon(page, lat, lon)` | Smooth drag to target |
| `wheel_to_zoom(page, target_zoom)` | Gradual zoom with scroll wheel |
| `human_scroll(page, direction, distance_px)` | Natural scrolling behavior |
| `random_mouse_movements(page, duration_s)` | Random mouse activity |
| `grid_sweep(page, center_lat, center_lon, zoom, rings, step_px, dwell_s, action_callback)` | Area scanning |

### Browser Functions

| Function | Description |
|----------|-------------|
| `launch_browser_desktop(...)` | Launch desktop browser |
| `launch_browser_mobile(...)` | Launch mobile browser |
| `create_worker_pool(ctx, worker_count)` | Create concurrent worker tabs |
| `setup_resource_blocking(ctx, block_types)` | Block heavy resources |

### Utility Functions

| Function | Description |
|----------|-------------|
| `random_delay(min_s, max_s)` | Generate random delay |
| `human_think_time(min_s, max_s)` | Human-like pause |
| `click_element_safely(page, selector)` | Safe click with timeout |
| `wait_for_element(page, selector)` | Wait for element |
| `generate_timestamp()` | Generate timestamp string |

---

## Project Structure

```
anti_bot_scraper/
├── anti_bot_core.py    # Main framework module
├── README.md           # This file
├── CHANGELOG.md        # Version history
└── LICENSE             # MIT License
```

---

## License

MIT License - Free to use, modify, and distribute with attribution.

---

**Star this repository if it helps with your projects!**
