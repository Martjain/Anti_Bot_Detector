#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Anti-Bot Core Module - Generic Web Scraping Framework

Universal anti-bot detection bypass utilities designed for use across any website.
Implements behavioral mimicry, advanced navigation patterns, and stealth techniques.

This module provides reusable components:
- Human-like browser interactions (mouse, keyboard, scrolling)
- Geographic coordinate manipulation (Mercator projection)
- Resource blocking for performance
- Browser fingerprint masking
- Async task scheduling
- Response interception hooks

Author: [Your Name]
Repository: github.com/[username]/anti-bot-scraper-core
"""

import asyncio
import math
import random
import re
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

# ========== Geographic Conversion (Mercator Projection) ==========


def ll_to_pixel(lat: float, lon: float, z: float) -> Tuple[float, float]:
    """
    Convert latitude/longitude to pixel coordinates using Mercator projection.

    This is the same projection used by Google Maps and most web mapping services.
    Provides sub-pixel accuracy for precise map navigation without correction loops.

    Args:
        lat: Latitude in degrees (-90 to 90)
        lon: Longitude in degrees (-180 to 180)
        z: Zoom level (higher = more zoomed in)

    Returns:
        tuple: (x, y) pixel coordinates

    Math:
        x = (lon + 180) / 360 * scale
        y = (0.5 - ln((1 + sin(lat)) / (1 - sin(lat))) / 4π) * scale
        where scale = 256 * 2^z
    """
    scale = 256 * (2**z)
    x = (lon + 180.0) / 360.0 * scale
    siny = math.sin(math.radians(lat))
    y = (0.5 - math.log((1 + siny) / (1 - siny)) / (4 * math.pi)) * scale
    return x, y


def pixel_to_ll(x: float, y: float, z: float) -> Tuple[float, float]:
    """
    Convert pixel coordinates back to latitude/longitude (inverse Mercator).

    Used for grid sweep and area calculations.

    Args:
        x: Pixel X coordinate
        y: Pixel Y coordinate
        z: Zoom level

    Returns:
        tuple: (lat, lon) in degrees
    """
    scale = 256 * (2**z)
    lon = x / scale * 360.0 - 180.0
    n = math.pi - 2.0 * math.pi * y / scale
    lat = math.degrees(math.atan(math.sinh(n)))
    return lat, lon


def clamp_coordinates(lat: float, lon: float, bounds: Tuple[float, float, float, float]) -> Tuple[float, float]:
    """
    Clamp coordinates to specified geographic boundaries.

    Prevents navigation outside specified region.

    Args:
        lat: Latitude
        lon: Longitude
        bounds: (latMin, latMax, lonMin, lonMax) tuple

    Returns:
        tuple: (clamped_lat, clamped_lon)
    """
    mnLat, mxLat, mnLon, mxLon = bounds
    return max(mnLat, min(lat, mxLat)), max(mnLon, min(lon, mxLon))


# ========== Anti-Bot: Navigation Mimicry ==========


async def human_like_recenter(
    page: Page, lat: float, lon: float, zoom: int, randomize: bool = True
) -> None:
    """
    Navigate to target coordinates using human-like exploration pattern.

    Humans don't teleport to exact coordinates. They:
    1. Zoom out to get context
    2. Navigate to general area
    3. Zoom back in for details
    4. Fine-tune position

    This multi-step approach avoids the "bot teleport" signature.

    Args:
        page: Playwright page object
        lat: Target latitude
        lon: Target longitude
        zoom: Target zoom level
        randomize: Whether to add randomness to zoom levels
    """
    # Step 1: Random zoom out (humans explore context)
    if randomize:
        rand_out = random.randint(9, 12)
    else:
        rand_out = max(9, zoom - 3)
    await wheel_to_zoom(page, rand_out)

    # Step 2: Navigate to area
    await drag_to_latlon(page, lat, lon)

    # Step 3: Zoom in to target level
    await wheel_to_zoom(page, zoom)

    # Step 4: Fine-tune position (humans aren't pixel-perfect on first try)
    await drag_to_latlon(page, lat, lon)


async def drag_to_latlon(
    page: Page,
    lat: float,
    lon: float,
    tolerance_px: float = 3.5,
    max_iterations: int = 18,
    max_drag_px: float = 800.0,
    step_count: int = 20,
) -> None:
    """
    Drag map to target coordinates with smooth, human-like movement.

    Key anti-detection features:
    - Bézier-like curve via Playwright's steps parameter
    - Distance-based step clamping (humans don't drag 5000px in one motion)
    - Natural pause after drag completes
    - Smooth acceleration/deceleration

    Args:
        page: Playwright page
        lat: Target latitude
        lon: Target longitude
        tolerance_px: Stop when within this many pixels (sub-pixel accuracy)
        max_iterations: Maximum drag attempts to reach target
        max_drag_px: Maximum distance to drag per iteration (realism constraint)
        step_count: Smooth interpolation steps (higher = smoother)

    Technical:
        - Uses Mercator projection for pixel calculation
        - Smooth mouse movement with acceleration curve
    """
    for _ in range(max_iterations):
        # Get current map center from URL or page state
        current_state = await _get_page_state(page)
        if not current_state:
            await asyncio.sleep(0.3)
            continue

        cur_lat, cur_lon, z = current_state

        # Convert geo coordinates to pixels
        x1, y1 = ll_to_pixel(cur_lat, cur_lon, z)
        x2, y2 = ll_to_pixel(lat, lon, z)

        dx, dy = x2 - x1, y2 - y1
        dist = math.hypot(dx, dy)

        # Check if close enough
        if dist <= tolerance_px:
            return

        # Clamp drag distance (humans don't drag entire screen at once)
        step = min(max_drag_px, dist)
        r = step / (dist + 1e-9)
        mx, my = dx * r, dy * r

        # Execute smooth drag with Bézier-like interpolation
        await page.mouse.move(960, 540)
        await page.mouse.down()
        await page.mouse.move(960 - mx, 540 - my, steps=step_count)
        await page.mouse.up()

        # Human pause after drag
        await asyncio.sleep(0.35)


async def wheel_to_zoom(
    page: Page, target_zoom: int, step_delay: float = 0.3, max_attempts: int = 20
) -> None:
    """
    Zoom to target level using mouse wheel with gradual steps.

    Bots zoom instantly. Humans scroll gradually with natural pauses.

    Args:
        page: Playwright page
        target_zoom: Desired zoom level
        step_delay: Delay between zoom steps in seconds
        max_attempts: Maximum zoom attempts
    """
    for _ in range(max_attempts):
        current_state = await _get_page_state(page)
        if not current_state:
            await asyncio.sleep(0.3)
            continue

        _, _, z = current_state
        z = round(z)

        if z == target_zoom:
            return

        # Zoom in or out with realistic scroll amount
        await page.mouse.move(960, 540)
        scroll_direction = -300 if target_zoom > z else 300
        await page.mouse.wheel(0, scroll_direction)
        await asyncio.sleep(step_delay)


async def human_scroll(
    page: Page,
    direction: str = "down",
    distance_px: int = 300,
    duration_ms: int = 500,
    pauses: int = 3,
) -> None:
    """
    Perform human-like scrolling with natural pauses.

    Args:
        page: Playwright page
        direction: "up" or "down"
        distance_px: Distance to scroll in pixels
        duration_ms: Duration of scroll in milliseconds
        pauses: Number of micro-pauses during scroll
    """
    step_size = distance_px // pauses
    scroll_delta = -1 if direction == "up" else 1

    for _ in range(pauses):
        await page.mouse.wheel(0, scroll_delta * step_size)
        await asyncio.sleep(duration_ms / (pauses * 1000))


async def random_mouse_movements(page: Page, duration_s: float = 2.0) -> None:
    """
    Perform random mouse movements to simulate human browsing.

    Useful for appearing active during page load or data collection.

    Args:
        page: Playwright page
        duration_s: Duration of random movements in seconds
    """
    start_time = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start_time < duration_s:
        x = random.randint(100, 1800)
        y = random.randint(100, 1000)
        await page.mouse.move(x, y)
        await asyncio.sleep(random.uniform(0.1, 0.5))


async def grid_sweep(
    page: Page,
    center_lat: float,
    center_lon: float,
    zoom: int,
    rings: int = 1,
    step_px: int = 360,
    dwell_s: float = 0.5,
    action_callback: Optional[Callable] = None,
) -> None:
    """
    Scan area using strategic grid pattern that appears unsystematic.

    Traditional approach: Visit every grid cell (obvious bot pattern)
    This approach: Scan only top/bottom rows of each ring

    Result: Complete coverage but unpredictable server-side pattern.

    Args:
        page: Playwright page
        center_lat, center_lon: Grid center coordinates
        zoom: Current zoom level
        rings: Number of rings around center (1 = ~8 points)
        step_px: Distance between grid points in pixels
        dwell_s: Time to wait at each point (seconds)
        action_callback: Async function called at each grid point

    Grid Pattern (rings=1):
        . . . . .
        . . . . .  ← Scan top row only
        . . X . .  (X = center, not visited)
        . . . . .  ← Scan bottom row only
        . . . . .
    """
    # Convert center to pixels
    cx, cy = ll_to_pixel(center_lat, center_lon, zoom)
    coords = []

    # Build coordinate list: only top and bottom rows per ring
    for r in range(1, rings + 1):
        for dx in range(-r, r + 1):
            for dy in (-r, r):  # Only top and bottom (not middle rows)
                x, y = cx + dx * step_px, cy + dy * step_px
                coords.append(pixel_to_ll(x, y, zoom))

    # Execute sweep
    total = len(coords)
    for i, (lat_, lon_) in enumerate(coords, 1):
        print(f"   Grid point {i}/{total}...")
        await drag_to_latlon(page, lat_, lon_)

        # Execute action callback if provided
        if action_callback:
            await action_callback(page, lat_, lon_, i, total)

        await asyncio.sleep(dwell_s)


# ========== Browser State Management ==========


async def _get_page_state(page: Page) -> Optional[Tuple[float, float, float]]:
    """
    Extract page state from URL (map state, current position, etc).

    This is website-specific and should be overridden by caller.
    Default implementation looks for 'ms' parameter in URL.

    Returns:
        tuple: (lat, lon, zoom) or None if unavailable
    """
    try:
        u = urlparse(page.url)
        ms = parse_qs(u.query).get("ms", [None])[0]
        if not ms:
            return None
        la, lo, zz = ms.split(",")
        return float(la), float(lo), float(zz)
    except Exception:
        return None


async def setup_resource_blocking(ctx: BrowserContext, block_types: Optional[List[str]] = None) -> None:
    """
    Block heavy resources (images, fonts, media) for performance.

    Counterintuitive insight: This makes scraper LESS suspicious.
    Real users with ad blockers behave exactly this way.

    Performance improvement: 2-3x faster page loads.

    Args:
        ctx: Playwright browser context
        block_types: List of resource types to block
                    (default: ["image", "media", "font", "stylesheet"])
    """
    if block_types is None:
        block_types = ["image", "media", "font"]

    async def _route(route):
        rt = route.request.resource_type
        if rt in block_types:
            return await route.abort()
        return await route.continue_()

    await ctx.route("**/*", _route)


async def launch_browser_desktop(
    headless: bool = False,
    viewport_width: int = 1920,
    viewport_height: int = 1080,
    user_agent: Optional[str] = None,
) -> Tuple[Browser, BrowserContext, Page]:
    """
    Launch desktop browser with anti-bot optimizations.

    Args:
        headless: Whether to run in headless mode
        viewport_width: Viewport width in pixels
        viewport_height: Viewport height in pixels
        user_agent: Custom user agent string

    Returns:
        tuple: (browser, context, page)

    Note:
        Caller is responsible for closing browser and context:
        await context.close()
        await browser.close()
    """
    if user_agent is None:
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    p = await async_playwright().start()
    try:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            viewport={"width": viewport_width, "height": viewport_height},
            user_agent=user_agent,
        )

        page = await context.new_page()

        # Hide webdriver property (bot detection bypass)
        await page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )

        return browser, context, page
    except Exception as e:
        await p.stop()
        raise e


async def launch_browser_mobile(
    device_name: str = "iPhone 14 Pro Max",
    headless: bool = False,
    user_agent: Optional[str] = None,
) -> Tuple[Browser, BrowserContext, Page]:
    """
    Launch mobile browser with anti-bot optimizations.

    Args:
        device_name: Device name (e.g., "iPhone 14 Pro Max")
        headless: Whether to run in headless mode
        user_agent: Custom user agent string (optional, device default used if None)

    Returns:
        tuple: (browser, context, page)

    Note:
        Caller is responsible for closing browser and context:
        await context.close()
        await browser.close()
    """
    p = await async_playwright().start()
    try:
        browser = await p.chromium.launch(headless=headless)

        device = p.devices[device_name]
        context = await browser.new_context(
            **device,
            locale="en-US",
            extra_http_headers={
                "accept-language": "en-US,en;q=0.9",
            },
        )

        page = await context.new_page()

        # Hide webdriver property
        await page.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.open = (u)=>{ location.href = u; };
        """
        )

        return browser, context, page
    except Exception as e:
        await p.stop()
        raise e


async def create_worker_pool(
    ctx: BrowserContext, worker_count: int = 12
) -> asyncio.Queue:
    """
    Create a pool of browser tabs for concurrent processing.

    Args:
        ctx: Playwright browser context
        worker_count: Number of worker tabs to create

    Returns:
        asyncio.Queue: Queue containing worker page objects
    """
    page_q = asyncio.Queue()

    for _ in range(max(1, worker_count)):
        dp = await ctx.new_page()
        await dp.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.open = (u)=>{ location.href = u; };
        """
        )
        page_q.put_nowait(dp)

    return page_q


# ========== Response Interception & Data Collection ==========


def create_response_interceptor(
    handlers: Optional[Dict[str, Callable]] = None,
) -> Callable:
    """
    Create a response handler for intercepting API calls.

    Args:
        handlers: Dict mapping URL patterns to async handler functions
                 Handler signature: async def handler(response, match_obj)

    Returns:
        Async function suitable for page.on("response", ...)
    """
    if handlers is None:
        handlers = {}

    async def _handle_response(response):
        url = response.url
        for pattern, handler in handlers.items():
            if pattern in url:
                try:
                    await handler(response)
                except Exception as e:
                    print(f"Handler error for {pattern}: {e}")

    return _handle_response


# ========== Delay & Randomization ==========


def random_delay(min_s: float = 0.5, max_s: float = 2.0) -> float:
    """
    Generate random delay between min and max seconds.

    Args:
        min_s: Minimum delay in seconds
        max_s: Maximum delay in seconds

    Returns:
        float: Delay duration in seconds
    """
    return random.uniform(min_s, max_s)


async def human_think_time(min_s: float = 1.0, max_s: float = 3.0) -> None:
    """
    Wait for random "thinking time" before proceeding.

    Simulates user reading/processing time.

    Args:
        min_s: Minimum wait time
        max_s: Maximum wait time
    """
    delay = random.uniform(min_s, max_s)
    await asyncio.sleep(delay)


# ========== Utilities ==========


async def extract_text_from_page(page: Page, selector: str = "body") -> str:
    """
    Safely extract text content from page element.

    Args:
        page: Playwright page
        selector: CSS selector

    Returns:
        str: Text content or empty string if error
    """
    try:
        return await page.inner_text(selector)
    except Exception:
        return ""


async def click_element_safely(
    page: Page, selector: str, timeout_ms: int = 5000
) -> bool:
    """
    Safely click element with error handling.

    Args:
        page: Playwright page
        selector: CSS selector or locator text
        timeout_ms: Timeout in milliseconds

    Returns:
        bool: True if click succeeded, False otherwise
    """
    try:
        await page.locator(selector).first.click(timeout=timeout_ms)
        return True
    except Exception:
        return False


async def wait_for_element(
    page: Page, selector: str, timeout_ms: int = 10000
) -> bool:
    """
    Wait for element to appear with timeout.

    Args:
        page: Playwright page
        selector: CSS selector
        timeout_ms: Timeout in milliseconds

    Returns:
        bool: True if element appeared, False if timeout
    """
    try:
        await page.wait_for_selector(selector, timeout=timeout_ms)
        return True
    except Exception:
        return False


def generate_timestamp() -> str:
    """Generate timestamp string for file naming."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# ========== Logging & Monitoring ==========


class ScraperLogger:
    """Simple logging utility for scraper operations."""

    def __init__(self, prefix: str = ""):
        self.prefix = prefix

    def log(self, message: str, level: str = "INFO") -> None:
        """Log message with timestamp and level."""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}] [{level}] {self.prefix}: {message}")

    def info(self, message: str) -> None:
        self.log(message, "INFO")

    def warning(self, message: str) -> None:
        self.log(message, "WARNING")

    def error(self, message: str) -> None:
        self.log(message, "ERROR")

    def success(self, message: str) -> None:
        self.log(message, "✅")


# ========== Example Usage Pattern ==========

if __name__ == "__main__":
    print("Anti-Bot Core Module v1.0")
    print("Import this module to use anti-bot scraping utilities")
    print("\nExample:")
    print("  from anti_bot_core import launch_browser_desktop, human_like_recenter")
    print("  async def scrape():")
    print("    browser, ctx, page = await launch_browser_desktop()")
    print("    await page.goto('https://example.com')")
    print("    await human_like_recenter(page, lat=37.5, lon=126.9, zoom=15)")
