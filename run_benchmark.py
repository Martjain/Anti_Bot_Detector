#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Anti-Bot Benchmark Runner

Main script to run benchmark tests against multiple websites.
"""

import argparse
import asyncio
import json
from pathlib import Path

from benchmark import BenchmarkTester


def load_config(config_path: str = "test_sites.json") -> dict:
    """Load test configuration from JSON file."""
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


async def run_tests(
    categories: list = None,
    iterations: int = 3,
    headless: bool = True,
    comparison: bool = False,
    config_path: str = "test_sites.json",
) -> None:
    """Run benchmark tests against configured websites."""
    config = load_config(config_path)
    tester = BenchmarkTester()

    if categories is None:
        categories = config["test_config"]["categories"]

    all_urls = []
    for category in categories:
        if category in config["test_websites"]:
            all_urls.extend(config["test_websites"][category])

    if not all_urls:
        print("No websites found to test.")
        return

    print(f"Starting benchmark tests against {len(all_urls)} websites...")
    print(f"Categories: {', '.join(categories)}")
    print(f"Iterations per site: {iterations}")
    print(f"Comparison mode: {comparison}")
    print("-" * 60)

    for site in all_urls:
        url = site["url"]
        name = site.get("name", url)
        print(f"\n📊 Testing: {name}")
        print(f"   URL: {url}")
        print(f"   Description: {site.get('description', 'N/A')}")

        if comparison:
            print("   Running comparison tests (anti-bot vs regular)...")
            anti_bot_results, regular_results = await tester.run_comparison_test(
                url, iterations=iterations, headless=headless
            )

            for i, result in enumerate(anti_bot_results):
                result.use_anti_bot = True
                tester.results.append(result)

            for i, result in enumerate(regular_results):
                result.use_anti_bot = False
                tester.results.append(result)

            anti_success = sum(1 for r in anti_bot_results if r.success)
            reg_success = sum(1 for r in regular_results if r.success)
            print(f"   ✅ Anti-bot: {anti_success}/{iterations} success")
            print(f"   🔄 Regular: {reg_success}/{iterations} success")
        else:
            for i in range(iterations):
                print(f"   Iteration {i + 1}/{iterations}...")
                result = await tester.test_website(url, use_anti_bot=True, headless=headless)
                result.use_anti_bot = True
                tester.results.append(result)
                
                if result.success:
                    print(f"   ✅ Success")
                else:
                    print(f"   ❌ Failed - {result.challenge_type or result.error_message}")

    print("\n" + "=" * 60)
    print("Benchmark tests complete!")
    print("=" * 60)

    summary = tester.get_summary_stats()
    print(f"\n📈 Summary Statistics:")
    print(f"   Total tests: {summary['total_tests']}")
    print(f"   Success rate: {summary['success_rate']}%")
    print(f"   Detection rate: {summary['detection_rate']}%")
    print(f"   Captcha rate: {summary['captcha_rate']}%")
    print(f"   Avg load time: {summary['avg_load_time_ms']}ms")
    print(f"   Avg elements: {summary['avg_elements_loaded']}")

    if summary['challenge_types']:
        print(f"\n🔒 Challenge Types Detected:")
        for challenge_type, count in summary['challenge_types'].items():
            print(f"   {challenge_type}: {count}")

    filepath = tester.save_results()
    print(f"\n💾 Results saved to: {filepath}")
    print(f"\n🚀 Launch dashboard:")
    print(f"   streamlit run dashboard.py")


def main():
    parser = argparse.ArgumentParser(
        description="Run anti-bot benchmark tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests with default settings
  python run_benchmark.py

  # Run only common targets
  python run_benchmark.py --categories common_targets

  # Run comparison tests (anti-bot vs regular)
  python run_benchmark.py --comparison

  # Run with visible browser (for debugging)
  python run_benchmark.py --no-headless

  # Run with more iterations
  python run_benchmark.py --iterations 5
        """
    )

    parser.add_argument(
        "--categories",
        nargs="+",
        choices=["common_targets", "bot_protected", "demo_sites"],
        help="Website categories to test (default: all)",
    )

    parser.add_argument(
        "--iterations",
        type=int,
        default=3,
        help="Number of iterations per website (default: 3)",
    )

    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run with visible browser (not headless)",
    )

    parser.add_argument(
        "--comparison",
        action="store_true",
        help="Run comparison tests (anti-bot vs regular scraping)",
    )

    parser.add_argument(
        "--config",
        default="test_sites.json",
        help="Path to configuration file (default: test_sites.json)",
    )

    args = parser.parse_args()

    asyncio.run(run_tests(
        categories=args.categories,
        iterations=args.iterations,
        headless=not args.no_headless,
        comparison=args.comparison,
        config_path=args.config,
    ))


if __name__ == "__main__":
    main()
