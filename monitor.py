#!/usr/bin/env python3
"""
Smart Shopper - Background Price Monitor
Run this alongside app.py to keep prices updated automatically.

    python monitor.py

It reads all active products from the DB, fetches live prices via
PriceFetcher, persists them, and emails alerts via Mailer.
"""
import time
import signal
import sys
from datetime import datetime
from pathlib import Path

# ── Allow running from project root ──────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

from scraper import fetcher, _load_config

# ── Optional mailer ───────────────────────────────────────────────────────────
try:
    from price_tracker.mailer import Mailer
    _mailer_available = True
except ImportError:
    _mailer_available = False
    print("⚠️  mailer.py not found — email alerts disabled")

# ── Signal handler for clean shutdown ─────────────────────────────────────────
running = True

def _handle_signal(sig, frame):
    global running
    print("\n\n🛑 Shutting down monitor…")
    running = False

signal.signal(signal.SIGINT,  _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


# ── Main loop ─────────────────────────────────────────────────────────────────
def main():
    global running

    cfg = _load_config()
    # check_interval in config is stored in minutes
    interval_minutes = int(cfg.get('check_interval', 5))
    interval_seconds = max(60, interval_minutes * 60)

    print("=" * 60)
    print("🛍️  Smart Shopper — Background Price Monitor")
    print("=" * 60)
    print(f"⏰ Check interval : {interval_minutes} minutes")
    print(f"📂 DB             : {Path(__file__).parent / 'data' / 'price_tracker.db'}")

    # Mailer setup
    mailer = None
    if _mailer_available:
        try:
            mailer = Mailer()
            mailer.log_in()
            if mailer.email_works:
                print("📧 Email alerts   : ✅ ready")
            else:
                print("📧 Email alerts   : ⚠️  not configured (set in Admin → Settings)")
        except Exception as e:
            print(f"📧 Email alerts   : ❌ {e}")

    serpapi_key = cfg.get('serpapi_key', '')
    if serpapi_key:
        print(f"🔑 SerpAPI        : ✅ key found")
    else:
        print(f"🔑 SerpAPI        : ⚠️  no key — direct scraping only")

    print("=" * 60)
    print("Press Ctrl+C to stop\n")

    while running:
        start = time.time()

        # Re-read config each cycle so interval / key changes apply live
        cfg = _load_config()
        fetcher._reload_key()

        results = fetcher.check_all()

        if mailer:
            fetcher.send_pending_alerts(mailer)

        elapsed = round(time.time() - start, 1)
        wait    = max(0, interval_seconds - elapsed)

        print(f"\n⏳ Next check in {interval_minutes} minutes  (last run: {elapsed}s)")
        print(f"   Sleeping until {datetime.fromtimestamp(time.time() + wait).strftime('%H:%M:%S')}\n")

        # Sleep in small chunks so Ctrl+C is responsive
        slept = 0
        while running and slept < wait:
            time.sleep(min(5, wait - slept))
            slept += 5

    print("👋 Monitor stopped.")


if __name__ == '__main__':
    main()
