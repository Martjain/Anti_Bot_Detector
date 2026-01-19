#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Anti-Bot Scraper - Generic Website Example

Demonstrates how to use the anti_bot_core module for scraping any website.
This example provides a template for creating custom scrapers.

Usage:
    python anti_bot_example.py
"""

import asyncio

from anti_bot_core import (
    ScraperLogger,
    create_worker_pool,
    grid_sweep,
    human_like_recenter,
    human_think_time,
    launch_browser_desktop,
    random_delay,
    setup_resource_blocking,
)


async def example_simple_scrape():
    """
    Simple example: Navigate to a website and extract data.
    """
    logger = ScraperLogger("SimpleExample")
    logger.info("Starting simple scrape...")

    # Launch browser
    browser, ctx, page = await launch_browser_desktop(headless=False)

    try:
        # Block heavy resources for speed
        await setup_resource_blocking(ctx)

        # Navigate to website
        logger.info("Navigating to example.com...")
        await page.goto("https://example.com")

        # Wait for human-like thinking time
        await human_think_time(1.0, 2.0)

        # Extract page content
        title = await page.title()
        logger.success(f"Page title: {title}")

        # Take screenshot
        await page.screenshot(path="example_screenshot.png")
        logger.success("Screenshot saved: example_screenshot.png")

    finally:
        await ctx.close()
        await browser.close()


async def example_with_navigation():
    """
    Example: Navigate with human-like patterns.
    This example shows how to use navigation utilities for map-based websites.
    """
    logger = ScraperLogger("NavigationExample")
    logger.info("Starting navigation example...")

    browser, ctx, page = await launch_browser_desktop(headless=False)

    try:
        await setup_resource_blocking(ctx)

        # Navigate to map-based website (e.g., Google Maps)
        logger.info("Navigating to map website...")
        await page.goto(
            "https://www.google.com/maps/@37.5608,126.9888,15z",
            wait_until="domcontentloaded",
        )

        # Wait for page to load
        await human_think_time(2.0, 3.0)

        # Perform human-like navigation
        logger.info("Performing human-like recenter...")
        target_lat, target_lon, target_zoom = 37.4419, 126.7996, 15
        await human_like_recenter(page, target_lat, target_lon, target_zoom)

        logger.success("Navigation complete")

    finally:
        await ctx.close()
        await browser.close()


async def example_with_parallel_workers():
    """
    Example: Use worker pool for parallel processing.
    Useful for scraping multiple items concurrently.
    """
    logger = ScraperLogger("WorkerPoolExample")
    logger.info("Starting worker pool example...")

    browser, ctx, page = await launch_browser_desktop(headless=False)

    try:
        await setup_resource_blocking(ctx)

        # Create worker pool
        worker_count = 4
        worker_pool = await create_worker_pool(ctx, worker_count)
        logger.info(f"Created {worker_count} worker tabs")

        # Simulate parallel tasks
        async def process_item(item_id: int) -> str:
            """Simulate processing an item with a worker"""
            worker_page = await worker_pool.get()
            try:
                logger.info(f"Processing item {item_id}...")
                await worker_page.goto(
                    f"https://example.com/item/{item_id}",
                    wait_until="domcontentloaded",
                )
                await human_think_time(0.5, 1.5)

                title = await worker_page.title()
                logger.success(f"Item {item_id}: {title}")
                return title

            finally:
                await worker_pool.put(worker_page)

        # Process items in parallel
        tasks = [process_item(i) for i in range(1, 5)]
        results = await asyncio.gather(*tasks)
        logger.success(f"Processed {len(results)} items")

    finally:
        await ctx.close()
        await browser.close()


async def example_with_response_interception():
    """
    Example: Intercept API responses to collect data.
    Useful for sites that load data via AJAX.
    """
    logger = ScraperLogger("ResponseInterceptionExample")
    logger.info("Starting response interception example...")

    browser, ctx, page = await launch_browser_desktop(headless=False)

    collected_data = []

    # Define response handler
    async def handle_api_response(response):
        """Intercept and process API responses"""
        if "/api/" in response.url:
            try:
                data = await response.json()
                logger.info(f"Intercepted API response: {response.url}")
                collected_data.append({
                    "url": response.url,
                    "timestamp": await asyncio.get_event_loop().time(),
                    "data": data,
                })
            except:
                pass

    try:
        await setup_resource_blocking(ctx)

        # Attach response interceptor
        page.on("response", handle_api_response)

        logger.info("Navigating to website...")
        await page.goto("https://example.com")

        # Wait for API calls to complete
        await human_think_time(3.0, 5.0)

        logger.success(f"Collected {len(collected_data)} API responses")

    finally:
        await ctx.close()
        await browser.close()


async def example_grid_sweep():
    """
    Example: Perform grid sweep for area scanning.
    Useful for map-based applications.
    """
    logger = ScraperLogger("GridSweepExample")
    logger.info("Starting grid sweep example...")

    browser, ctx, page = await launch_browser_desktop(headless=False)

    try:
        await setup_resource_blocking(ctx)

        # Navigate to map
        await page.goto("https://www.google.com/maps/", wait_until="domcontentloaded")
        await human_think_time(2.0, 3.0)

        # Define action to perform at each grid point
        async def grid_action(page, lat, lon, index, total):
            logger.info(f"Grid point {index}/{total} at ({lat:.4f}, {lon:.4f})")
            # Perform some action here (screenshot, scrape, etc)
            await human_think_time(0.5, 1.0)

        # Perform grid sweep
        center_lat, center_lon = 37.5608, 126.9888
        zoom = 15
        rings = 2

        logger.info(f"Scanning area with {rings} rings...")
        await grid_sweep(
            page,
            center_lat=center_lat,
            center_lon=center_lon,
            zoom=zoom,
            rings=rings,
            step_px=500,
            dwell_s=1.0,
            action_callback=grid_action,
        )

        logger.success("Grid sweep complete")

    finally:
        await ctx.close()
        await browser.close()


async def main():
    """Run all examples"""
    print("\n" + "="*70)
    print("Anti-Bot Scraper - Generic Website Examples")
    print("="*70 + "\n")

    print("Choose an example to run:")
    print("1. Simple scrape")
    print("2. Navigation example")
    print("3. Parallel workers")
    print("4. Response interception")
    print("5. Grid sweep")
    print("0. Exit")

    choice = input("\nEnter your choice: ").strip()

    examples = {
        "1": example_simple_scrape,
        "2": example_with_navigation,
        "3": example_with_parallel_workers,
        "4": example_with_response_interception,
        "5": example_grid_sweep,
    }

    if choice in examples:
        print(f"\nRunning: {examples[choice].__name__}\n")
        try:
            await examples[choice]()
        except Exception as e:
            print(f"Error: {e}")
    elif choice != "0":
        print("Invalid choice")


if __name__ == "__main__":
    asyncio.run(main())
