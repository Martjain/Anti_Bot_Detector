#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Anti-Bot Benchmark Module

Tests anti-bot scraper effectiveness against multiple websites.
Measures detection rates, success metrics, and various anti-bot challenge indicators.
"""

import asyncio
import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from playwright.async_api import Page, BrowserContext
from anti_bot_core import launch_browser_desktop, setup_resource_blocking, ScraperLogger


@dataclass
class BenchmarkResult:
    """Single test result for a website."""
    url: str
    domain: str
    timestamp: str
    success: bool
    http_status: Optional[int]
    load_time_ms: float
    detected_by_bot_protection: bool
    captcha_present: bool
    challenge_type: Optional[str]
    js_executed: bool
    elements_loaded: int
    total_bytes: int
    blocked_resources: int
    user_agent: str
    error_message: Optional[str] = None
    notes: str = ""


@dataclass
class DetectionIndicators:
    """Detection indicators found on the page."""
    has_cloudflare_challenge: bool = False
    has_akamai_challenge: bool = False
    has_recaptcha: bool = False
    has_hcaptcha: bool = False
    has_cloudflare_turnstile: bool = False
    has_error_page: bool = False
    has_access_denied: bool = False
    has_rate_limit: bool = False
    has_bot_detection_text: bool = False
    challenge_page_url: Optional[str] = None


class BenchmarkTester:
    """Tests anti-bot scraper against multiple websites."""

    CHALLENGE_SELECTORS = {
        "cloudflare": [
            "div.cf-browser-verification",
            "div#challenge-form",
            "form[action*='cdn-cgi/l/chk_jschl']",
            "div[data-ray]",
        ],
        "akamai": [
            "div#akamai-challenge",
            "script[src*='akamai']",
            "iframe[src*='akamai']",
        ],
        "recaptcha": [
            "div.g-recaptcha",
            "div#recaptcha",
            "iframe[src*='recaptcha']",
        ],
        "hcaptcha": [
            "div#hcaptcha",
            "iframe[src*='hcaptcha']",
        ],
        "turnstile": [
            "div#turnstile-wrapper",
            "iframe[src*='turnstile']",
        ],
        "access_denied": [
            "body:has-text('Access Denied')",
            "body:has-text('Forbidden')",
            "body:has-text('403')",
            "h1:has-text('Access Denied')",
        ],
        "rate_limit": [
            "body:has-text('Rate Limit')",
            "body:has-text('Too Many Requests')",
            "body:has-text('429')",
        ],
        "error_page": [
            "body:has-text('Error')",
            "body:has-text('Something went wrong')",
            ".error-page",
        ],
        "bot_detection": [
            "body:has-text('bot')",
            "body:has-text('suspicious')",
            "body:has-text('automated')",
            "body:has-text('unusual traffic')",
        ],
    }

    def __init__(self, results_dir: str = "benchmark_results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        self.logger = ScraperLogger("Benchmark")
        self.results: List[BenchmarkResult] = []

    async def detect_challenges(self, page: Page) -> DetectionIndicators:
        """Detect various bot protection challenges on the page."""
        indicators = DetectionIndicators()

        for challenge_type, selectors in self.CHALLENGE_SELECTORS.items():
            for selector in selectors:
                try:
                    element = page.locator(selector)
                    count = await element.count()
                    if count > 0:
                        if challenge_type == "cloudflare":
                            indicators.has_cloudflare_challenge = True
                        elif challenge_type == "akamai":
                            indicators.has_akamai_challenge = True
                        elif challenge_type == "recaptcha":
                            indicators.has_recaptcha = True
                        elif challenge_type == "hcaptcha":
                            indicators.has_hcaptcha = True
                        elif challenge_type == "turnstile":
                            indicators.has_cloudflare_turnstile = True
                        elif challenge_type == "access_denied":
                            indicators.has_access_denied = True
                        elif challenge_type == "rate_limit":
                            indicators.has_rate_limit = True
                        elif challenge_type == "error_page":
                            indicators.has_error_page = True
                        elif challenge_type == "bot_detection":
                            indicators.has_bot_detection_text = True
                except Exception:
                    continue

        if indicators.has_cloudflare_challenge or indicators.has_akamai_challenge:
            indicators.challenge_page_url = page.url

        return indicators

    async def count_loaded_elements(self, page: Page) -> int:
        """Count number of elements loaded on the page."""
        try:
            return await page.locator("*").count()
        except Exception:
            return 0

    async def check_js_execution(self, page: Page) -> bool:
        """Check if JavaScript executed properly."""
        try:
            result = await page.evaluate("window !== undefined && typeof window !== 'undefined'")
            return bool(result)
        except Exception:
            return False

    async def test_website(
        self,
        url: str,
        use_anti_bot: bool = True,
        headless: bool = True,
        timeout_ms: int = 30000,
    ) -> BenchmarkResult:
        """Test a single website with anti-bot scraper."""
        domain = urlparse(url).netloc
        start_time = time.time()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.logger.info(f"Testing {url} (anti-bot: {use_anti_bot})")

        browser = None
        context = None
        page = None

        try:
            if use_anti_bot:
                browser, context, page = await launch_browser_desktop(headless=headless)
                await setup_resource_blocking(context)
            else:
                from playwright.async_api import async_playwright
                p = await async_playwright().start()
                browser = await p.chromium.launch(headless=headless)
                context = await browser.new_context()
                page = await context.new_page()

            response = await page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
            load_time = (time.time() - start_time) * 1000

            http_status = response.status if response else None
            page_text = await page.content()

            detection = await self.detect_challenges(page)
            js_executed = await self.check_js_execution(page)
            elements_loaded = await self.count_loaded_elements(page)

            total_bytes = 0
            blocked_resources = 0

            success = (
                not detection.has_cloudflare_challenge
                and not detection.has_akamai_challenge
                and not detection.has_access_denied
                and not detection.has_rate_limit
                and http_status not in [403, 429, 503]
            )

            captcha_present = (
                detection.has_recaptcha
                or detection.has_hcaptcha
                or detection.has_cloudflare_turnstile
            )

            challenge_type = None
            if detection.has_cloudflare_challenge:
                challenge_type = "Cloudflare"
            elif detection.has_akamai_challenge:
                challenge_type = "Akamai"
            elif detection.has_recaptcha:
                challenge_type = "reCAPTCHA"
            elif detection.has_hcaptcha:
                challenge_type = "hCaptcha"
            elif detection.has_cloudflare_turnstile:
                challenge_type = "Cloudflare Turnstile"

            user_agent = await page.evaluate("navigator.userAgent")

            notes = []
            if detection.has_bot_detection_text:
                notes.append("Bot detection text found")
            if detection.has_error_page:
                notes.append("Error page detected")
            if not js_executed:
                notes.append("JavaScript execution failed")

            result = BenchmarkResult(
                url=url,
                domain=domain,
                timestamp=timestamp,
                success=success,
                http_status=http_status,
                load_time_ms=round(load_time, 2),
                detected_by_bot_protection=challenge_type is not None,
                captcha_present=captcha_present,
                challenge_type=challenge_type,
                js_executed=js_executed,
                elements_loaded=elements_loaded,
                total_bytes=total_bytes,
                blocked_resources=blocked_resources,
                user_agent=user_agent,
                notes="; ".join(notes),
            )

            self.logger.success(f"Test complete: {success} | {challenge_type or 'No challenge'}")

        except Exception as e:
            load_time = (time.time() - start_time) * 1000
            result = BenchmarkResult(
                url=url,
                domain=domain,
                timestamp=timestamp,
                success=False,
                http_status=None,
                load_time_ms=round(load_time, 2),
                detected_by_bot_protection=False,
                captcha_present=False,
                challenge_type=None,
                js_executed=False,
                elements_loaded=0,
                total_bytes=0,
                blocked_resources=0,
                user_agent="",
                error_message=str(e),
            )
            self.logger.error(f"Test failed: {e}")

        finally:
            if page:
                await page.close()
            if context:
                await context.close()
            if browser:
                await browser.close()

        return result

    async def run_comparison_test(
        self,
        url: str,
        iterations: int = 3,
        headless: bool = True,
    ) -> Tuple[List[BenchmarkResult], List[BenchmarkResult]]:
        """Run comparison tests with and without anti-bot measures."""
        anti_bot_results = []
        regular_results = []

        for i in range(iterations):
            self.logger.info(f"Iteration {i + 1}/{iterations}")
            
            result = await self.test_website(url, use_anti_bot=True, headless=headless)
            anti_bot_results.append(result)
            
            regular_result = await self.test_website(url, use_anti_bot=False, headless=headless)
            regular_results.append(regular_result)
            
            await asyncio.sleep(2)

        return anti_bot_results, regular_results

    def save_results(self, filename: Optional[str] = None) -> str:
        """Save results to JSON file."""
        if not filename:
            filename = f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = self.results_dir / filename
        
        data = [asdict(r) for r in self.results]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Results saved to {filepath}")
        return str(filepath)

    def load_results(self, filepath: str) -> None:
        """Load results from JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        self.results = [BenchmarkResult(**item) for item in data]
        self.logger.info(f"Loaded {len(self.results)} results from {filepath}")

    def get_summary_stats(self) -> Dict:
        """Calculate summary statistics from results."""
        if not self.results:
            return {}

        total = len(self.results)
        success_count = sum(1 for r in self.results if r.success)
        detected_count = sum(1 for r in self.results if r.detected_by_bot_protection)
        captcha_count = sum(1 for r in self.results if r.captcha_present)

        avg_load_time = sum(r.load_time_ms for r in self.results) / total
        avg_elements = sum(r.elements_loaded for r in self.results) / total

        by_domain = {}
        for r in self.results:
            if r.domain not in by_domain:
                by_domain[r.domain] = {"total": 0, "success": 0, "detected": 0}
            by_domain[r.domain]["total"] += 1
            if r.success:
                by_domain[r.domain]["success"] += 1
            if r.detected_by_bot_protection:
                by_domain[r.domain]["detected"] += 1

        challenge_types = {}
        for r in self.results:
            if r.challenge_type:
                challenge_types[r.challenge_type] = challenge_types.get(r.challenge_type, 0) + 1

        return {
            "total_tests": total,
            "success_rate": round(success_count / total * 100, 2),
            "detection_rate": round(detected_count / total * 100, 2),
            "captcha_rate": round(captcha_count / total * 100, 2),
            "avg_load_time_ms": round(avg_load_time, 2),
            "avg_elements_loaded": round(avg_elements, 2),
            "by_domain": by_domain,
            "challenge_types": challenge_types,
        }
