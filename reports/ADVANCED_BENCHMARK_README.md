# Advanced Bot Detection Benchmark

Test your anti-bot scraper against websites with enterprise-grade bot protection.

## Overview

This benchmark tests your script against **20+ real-world websites** that use advanced bot detection systems including:

- **Akamai Bot Manager**
- **Cloudflare Bot Management**
- **Enterprise WAF (Web Application Firewall)**
- **Custom Bot Detection Rules**

These are the same protections used by major e-commerce sites, betting platforms, and media companies.

## Websites by Category

### 🛍️ E-Commerce (Akamai Protected)
- Converse
- Woolworths Australia

### 🛍️ E-Commerce (Cloudflare Protected)
- Sam's Club
- Harley-Davidson
- Pearson

### 🎲 Betting & Gambling
- FlashScore USA
- Bet365
- DraftKings
- FanDuel
- Unibet

### ⚽ Sports & Live Scores
- ESPN
- CBS Sports
- Sky Sports
- Bleacher Report

### 💰 Other Platforms
- Fahorro
- Temu Mexico
- X (Twitter)
- LinkedIn
- Skyscanner

**Total:** 21 websites

## Running the Benchmark

### Quick Start

```bash
python run_advanced_benchmark.py
```

### Expected Duration

- **Per website:** ~2-3 minutes (2 iterations × 45s timeout)
- **Total time:** ~15-20 minutes
- **Tests:** 42 total tests (21 websites × 2 iterations)

### Using the Original Runner

You can also use the standard benchmark runner:

```bash
python run_benchmark.py --config test_sites_advanced.json --iterations 2
```

### Run Specific Categories

```bash
python run_benchmark.py --config test_sites_advanced.json --categories ecommerce_cloudflare betting_gambling
```

### Run with Visible Browser (Debug Mode)

```bash
python run_benchmark.py --config test_sites_advanced.json --no-headless --iterations 1
```

### Run Comparison Tests

Test anti-bot scraper vs regular headless browser:

```bash
python run_benchmark.py --config test_sites_advanced.json --comparison --iterations 2
```

## Results

Results are saved to `benchmark_results/advanced_benchmark.json`.

### View Results in Dashboard

```bash
streamlit run dashboard.py
```

## What to Expect

### Likely Successes

Your script should handle these well:
- Sam's Club (Cloudflare)
- Harley-Davidson (Cloudflare)
- LinkedIn (Cloudflare - previously passed)
- Skyscanner

### Likely Challenges

These may trigger detection:
- Bet365 (Enterprise-grade protection)
- DraftKings (Enterprise WAF)
- FanDuel (Geo-restricted, heavy protection)
- X/Twitter (Rate limiting, auth wall)
- Converse (Akamai Bot Manager)
- Woolworths Australia (Akamai + Geo)

### Uncertain

Results will vary:
- FlashScore USA (Cloudflare - variable)
- ESPN (Mixed protection levels)
- Temu Mexico (Cloudflare - region-dependent)
- Pearson (Cloudflare - enterprise)

## Interpreting Results

### Success Indicators

✅ **HTTP 200-299** - Page loaded successfully  
✅ **No challenge detected** - Passed bot protection  
✅ **JavaScript executed** - Dynamic content loaded  
✅ **Elements loaded** - Content present

### Failure Indicators

❌ **HTTP 403/429** - Blocked or rate limited  
❌ **Challenge detected** - Triggered bot protection  
❌ **Error page** - Redirection to block page  
❌ **Low element count** - Blocked from content

### Expected Behaviors

**Not Failures:**
- Geo-restriction errors (expected for US-only sites)
- Auth wall redirects (not a detection failure)
- Cookie consent modals (normal behavior)

**Potential Improvements:**
- Rate limiting errors (need longer delays)
- Captcha challenges (need captcha solving)
- Fingerprint detection (need more obfuscation)

## Configuration

Edit `test_sites_advanced.json` to:

- Add/remove websites
- Change iteration count
- Adjust timeout and delays
- Modify expected challenges

```json
{
  "test_config": {
    "iterations": 2,              // Tests per website
    "headless": true,             // Run headless or visible
    "timeout_ms": 45000,          // Max wait time per page
    "delay_between_tests": 3,     // Seconds between tests
    "categories": [...]           // Categories to test
  }
}
```

## Troubleshooting

### Tests Take Too Long

Increase timeout but reduce iterations:

```json
{
  "timeout_ms": 60000,
  "iterations": 1
}
```

### Many Timeouts

Some sites block headless browsers entirely. Try:

```bash
python run_benchmark.py --config test_sites_advanced.json --no-headless
```

### All Sites Fail

Check:
- Internet connection
- DNS resolution
- Firewall/proxy settings
- Browser installation

### View Browser in Action

Run single site with visible browser:

```bash
python run_benchmark.py --config test_sites_advanced.json --no-headless --categories ecommerce_cloudflare --iterations 1
```

## Comparison with Previous Results

After running, compare with your first benchmark (`benchmark_20260119_125702.json`):

**Previous:**
- 92% success rate
- Passed basic protections
- Failed on fingerprinting

**Advanced:**
- Expected lower success rate
- Tests enterprise protections
- Identifies new improvement areas

## Next Steps

Based on results, you may need to:

1. **Add Proxy Rotation** - For IP-based blocking
2. **Improve Fingerprints** - For detection by canvas/WebGL
3. **Add Captcha Solving** - For challenge pages
4. **Adjust Rate Limiting** - For 429 errors
5. **Handle Geo-Restrictions** - For regional content

## Notes

- Some sites geo-restrict content (Betting, DraftKings, FanDuel)
- Results may vary by time and server load
- Multiple iterations provide more accurate data
- Always respect robots.txt and terms of service

## Dashboard Features

The dashboard (`dashboard.py`) shows:

- Success rate by domain
- Challenge types encountered
- Load time distributions
- HTTP status codes
- Comparison charts (if using --comparison)
- Timeline of all tests

Export data as CSV for further analysis.

---

**Good luck!** These are real-world, well-protected sites. Any successes here demonstrate significant anti-bot capabilities.
