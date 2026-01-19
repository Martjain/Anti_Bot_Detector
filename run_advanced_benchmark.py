#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Bot Detection Benchmark Runner

Quick script to run tests against advanced bot detection sites.
"""

import asyncio
import sys

from benchmark import BenchmarkTester


async def run_advanced_tests():
    """Run advanced bot detection tests."""
    print("=" * 60)
    print("ADVANCED BOT DETECTION BENCHMARK")
    print("=" * 60)
    print("\nThis will test your anti-bot scraper against 20+ websites")
    print("with enterprise-grade protection (Akamai, Cloudflare, etc.)")
    print("\nExpected duration: ~15-20 minutes")
    print("\nPress Ctrl+C to cancel")
    print("-" * 60)

    tester = BenchmarkTester()
    
    import json
    with open("test_sites_advanced.json", "r") as f:
        config = json.load(f)
    
    test_websites = config["test_websites"]
    test_config = config["test_config"]
    
    all_urls = []
    for category, sites in test_websites.items():
        all_urls.extend(sites)

    print(f"\n📊 Testing {len(all_urls)} websites...")
    print(f"   Iterations per site: {test_config['iterations']}")
    print(f"   Headless mode: {test_config['headless']}")
    print(f"   Timeout: {test_config['timeout_ms']}ms")
    print(f"   Delay between tests: {test_config['delay_between_tests']}s")
    print("-" * 60)

    for i, site in enumerate(all_urls, 1):
        url = site["url"]
        name = site.get("name", url)
        print(f"\n[{i}/{len(all_urls)}] Testing: {name}")
        print(f"    URL: {url}")
        print(f"    Expected: {site.get('expected_challenges', 'N/A')}")
        
        for j in range(test_config["iterations"]):
            print(f"    Iteration {j + 1}/{test_config['iterations']}...", end=" ")
            
            result = await tester.test_website(
                url,
                use_anti_bot=True,
                headless=test_config["headless"],
                timeout_ms=test_config["timeout_ms"]
            )
            
            tester.results.append(result)
            
            if result.success:
                print(f"✅ Success ({result.load_time_ms}ms)")
            else:
                print(f"❌ Failed - {result.challenge_type or result.error_message}")
            
            if j < test_config["iterations"] - 1:
                await asyncio.sleep(test_config["delay_between_tests"])

    print("\n" + "=" * 60)
    print("ADVANCED BENCHMARK COMPLETE!")
    print("=" * 60)

    summary = tester.get_summary_stats()
    print(f"\n📈 Summary Statistics:")
    print(f"   Total tests: {summary['total_tests']}")
    print(f"   Success rate: {summary['success_rate']}%")
    print(f"   Detection rate: {summary['detection_rate']}%")
    print(f"   Captcha rate: {summary['captcha_rate']}%")
    print(f"   Avg load time: {summary['avg_load_time_ms']}ms")
    print(f"   Avg elements: {summary['avg_elements_loaded']}")

    if summary['by_domain']:
        print(f"\n📊 Results by Domain:")
        for domain, stats in summary['by_domain'].items():
            success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"   {domain}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")

    if summary['challenge_types']:
        print(f"\n🔒 Challenge Types Detected:")
        for challenge_type, count in summary['challenge_types'].items():
            print(f"   {challenge_type}: {count}")

    filepath = tester.save_results("advanced_benchmark.json")
    print(f"\n💾 Results saved to: {filepath}")
    print(f"\n🚀 Launch dashboard:")
    print(f"   streamlit run dashboard.py")


if __name__ == "__main__":
    try:
        asyncio.run(run_advanced_tests())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
