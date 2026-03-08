"""
settings.py — Scrapy project settings for data_gathering spider.
"""
from datetime import datetime
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parents[3]

timestamp = datetime.now().strftime("%Y%m%d_%H%M")

# Raw data output — one timestamped file per crawl run.
FEEDS = {
    str(BASE_DIR / "data" / "raw" / f"notebooks_{timestamp}.jsonl"): {
        "format": "jsonlines",
        "encoding": "utf8",
        "overwrite": True,
    }
}

# ── Spider settings ────────────────────────────────────────────────────────
BOT_NAME = "data_gathering"

SPIDER_MODULES = ["data_gathering.spiders"]
NEWSPIDER_MODULE = "data_gathering.spiders"

# Identifies the bot in request headers. Use a realistic UA to avoid blocking.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/145.0.0.0 Safari/537.36"
)

# Respect crawl rate limits (1 request/second per domain).
# NOTE: robots.txt is disabled because Mercado Livre blocks all bots via
# robots.txt even though the data is publicly accessible. This is a portfolio
# project for educational use only.
ROBOTSTXT_OBEY = False
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 1

# Required by Scrapy >= 2.6 to avoid deprecation warnings.
FEED_EXPORT_ENCODING = "utf-8"

ADDONS = {}
