#!/usr/bin/env python3
"""
Smart Shopper - Price Scraper
Fetches real prices via SerpAPI (primary) and direct scraping (fallback).
Persists every result to the SQLite database automatically.
"""
import re
import time
import json
import sqlite3
import requests
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent   # smart-shopper directory
DB_PATH  = BASE_DIR / 'data' / 'price_tracker.db'
CFG_PATH = BASE_DIR / 'config.json'

DB_PATH.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'en-IN,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def _load_config() -> dict:
    try:
        if CFG_PATH.exists():
            return json.loads(CFG_PATH.read_text())
    except Exception:
        pass
    return {}

def _clean_price(text) -> float | None:
    """Parse '₹62,999' or '62999.0' → 62999.0"""
    if text is None:
        return None
    s = re.sub(r'[₹$€£,\s]', '', str(text))
    nums = re.findall(r'\d+\.?\d*', s)
    if nums:
        val = float(nums[0])
        return val if val > 1 else None   # ignore decimal-only noise
    return None

def _detect_site(url: str) -> str:
    url = url.lower()
    if 'amazon.in' in url or 'amazon.com' in url: return 'Amazon India'
    if 'flipkart.com' in url:   return 'Flipkart'
    if 'meesho.com' in url:     return 'Meesho'
    if 'myntra.com' in url:     return 'Myntra'
    if 'snapdeal.com' in url:   return 'Snapdeal'
    return 'Other'

def _extract_asin(url: str) -> str | None:
    m = re.search(r'/dp/([A-Z0-9]{10})', url)
    return m.group(1) if m else None


# ── Database helpers ──────────────────────────────────────────────────────────
def _get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def _persist_price(product_id: int, price: float, source: str):
    """Write price to DB and update product row."""
    with _get_db() as conn:
        # current state
        row = conn.execute(
            'SELECT current_price, lowest_price, highest_price, target_price, name '
            'FROM products WHERE id=?', (product_id,)
        ).fetchone()
        if not row:
            return

        low  = min(price, row['lowest_price'])  if row['lowest_price']  else price
        high = max(price, row['highest_price']) if row['highest_price'] else price

        conn.execute(
            'UPDATE products SET current_price=?, lowest_price=?, highest_price=?, '
            'last_checked=CURRENT_TIMESTAMP WHERE id=?',
            (price, low, high, product_id)
        )
        conn.execute(
            'INSERT INTO price_history (product_id, price, source) VALUES (?,?,?)',
            (product_id, price, source)
        )

        # auto-create alert if price hit target
        if price <= row['target_price']:
            existing = conn.execute(
                'SELECT id FROM alerts WHERE product_id=? AND new_price=? '
                'AND sent_at >= datetime("now","-1 hour")',
                (product_id, price)
            ).fetchone()
            if not existing:
                conn.execute(
                    'INSERT INTO alerts (product_id, old_price, new_price, message) '
                    'VALUES (?,?,?,?)',
                    (product_id, row['current_price'], price,
                     f"Price dropped to ₹{price:,.0f} — alert was ₹{row['target_price']:,.0f}")
                )
                print(f"🚨 ALERT created for {row['name']} — ₹{price:,.0f}")


# ── SerpAPI ───────────────────────────────────────────────────────────────────
def _serpapi_google_shopping(query: str, serpapi_key: str) -> list[dict]:
    """
    Search Google Shopping via SerpAPI.
    Returns list of {title, price, source, link, image, rating, reviews}
    """
    try:
        resp = requests.get(
            'https://serpapi.com/search',
            params={
                'engine':   'google_shopping',
                'q':        query + ' India',
                'gl':       'in',
                'hl':       'en',
                'api_key':  serpapi_key,
                'num':      20,
            },
            timeout=20
        )
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data.get('shopping_results', []):
            price = _clean_price(item.get('extracted_price') or item.get('price'))
            if not price:
                continue
            results.append({
                'title':   item.get('title', ''),
                'price':   price,
                'source':  item.get('source', 'Unknown'),
                'link':    item.get('link', ''),
                'image':   item.get('thumbnail', ''),
                'rating':  item.get('rating'),
                'reviews': item.get('reviews'),
            })
        print(f"✅ SerpAPI Google Shopping: {len(results)} results for '{query}'")
        return results
    except Exception as e:
        print(f"❌ SerpAPI Google Shopping error: {e}")
        return []


def _serpapi_amazon_product(asin: str, serpapi_key: str) -> dict | None:
    """
    Fetch a single Amazon product by ASIN via SerpAPI amazon engine.
    Returns {name, price, rating, reviews, availability, image, source}
    """
    try:
        resp = requests.get(
            'https://serpapi.com/search',
            params={
                'engine':        'amazon_product',
                'asin':          asin,
                'amazon_domain': 'amazon.in',
                'api_key':       serpapi_key,
            },
            timeout=20
        )
        resp.raise_for_status()
        data = resp.json()

        if 'error' in data:
            print(f"❌ SerpAPI amazon_product error: {data['error']}")
            return None

        # Price lives in different places depending on the product
        price = None
        pr = data.get('product_results') or data.get('product_result', {})
        if isinstance(pr, dict):
            # Try nested paths in priority order
            candidates = [
                pr.get('price'),
                pr.get('prices', [{}])[0].get('value') if isinstance(pr.get('prices'), list) else None,
                (pr.get('buybox_winner') or {}).get('price', {}).get('value'),
                data.get('product_details', {}).get('Price'),
                data.get('product_details', {}).get('M.R.P.'),
            ]
            for c in candidates:
                price = _clean_price(c)
                if price:
                    break

            title = pr.get('title') or data.get('search_metadata', {}).get('query', 'Unknown')
            image = (pr.get('media') or [{}])[0].get('link', '') if isinstance(pr.get('media'), list) else ''

            if price:
                print(f"✅ SerpAPI Amazon product: {title[:50]} — ₹{price:,.0f}")
                return {
                    'name':         title,
                    'price':        price,
                    'rating':       pr.get('rating'),
                    'reviews':      pr.get('reviews_count'),
                    'availability': pr.get('availability', {}).get('raw', 'In Stock')
                                    if isinstance(pr.get('availability'), dict)
                                    else pr.get('availability', 'In Stock'),
                    'image':        image,
                    'source':       'SerpAPI Amazon',
                }
        print("⚠️ SerpAPI amazon_product: could not parse price from response")
        return None
    except Exception as e:
        print(f"❌ SerpAPI amazon_product error: {e}")
        return None


# ── Direct scraping fallbacks ─────────────────────────────────────────────────
def _scrape_amazon(url: str) -> dict | None:
    """Direct Amazon India scraping fallback."""
    try:
        from bs4 import BeautifulSoup
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.content, 'html.parser')

        # Title
        title_el = soup.select_one('#productTitle')
        title = title_el.get_text(strip=True) if title_el else None

        # Price — Amazon uses several selectors
        price = None
        for sel in [
            '.a-price .a-offscreen',      # most reliable
            '#priceblock_ourprice',
            '#priceblock_dealprice',
            '.a-price-whole',
        ]:
            el = soup.select_one(sel)
            if el:
                price = _clean_price(el.get_text())
                if price:
                    break

        if title and price:
            print(f"✅ Direct Amazon scrape: {title[:50]} — ₹{price:,.0f}")
            return {'name': title, 'price': price, 'source': 'Amazon Direct'}
    except Exception as e:
        print(f"❌ Amazon scrape error: {e}")
    return None


def _scrape_flipkart(url: str) -> dict | None:
    """Direct Flipkart scraping fallback."""
    try:
        from bs4 import BeautifulSoup
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.content, 'html.parser')

        title_el = soup.select_one('.B_NuCI') or soup.select_one('h1.yhB1nd')
        title = title_el.get_text(strip=True) if title_el else None

        price = None
        for sel in ['._30jeq3', '._16Jk6d', '.CEmiEU']:
            el = soup.select_one(sel)
            if el:
                price = _clean_price(el.get_text())
                if price:
                    break

        if title and price:
            print(f"✅ Direct Flipkart scrape: {title[:50]} — ₹{price:,.0f}")
            return {'name': title, 'price': price, 'source': 'Flipkart Direct'}
    except Exception as e:
        print(f"❌ Flipkart scrape error: {e}")
    return None


# ── Main public API ───────────────────────────────────────────────────────────
class PriceFetcher:
    """
    Public interface used by the monitor and Flask app.
    """

    def __init__(self):
        cfg = _load_config()
        self.serpapi_key = cfg.get('serpapi_key', '')

    def _reload_key(self):
        """Re-read config so admin UI key updates take effect without restart."""
        cfg = _load_config()
        self.serpapi_key = cfg.get('serpapi_key', '')

    # ── Search ────────────────────────────────────────────────────────────────
    def search(self, query: str) -> list[dict]:
        """Search Google Shopping. Returns list of product results."""
        self._reload_key()
        if self.serpapi_key:
            results = _serpapi_google_shopping(query, self.serpapi_key)
            if results:
                return results
        print("⚠️ No SerpAPI key or no results — returning empty search")
        return []

    def compare(self, query: str) -> list[dict]:
        """Like search() but grouped by cheapest-per-source."""
        results = self.search(query)
        by_source: dict[str, dict] = {}
        for r in results:
            src = r['source']
            if src not in by_source or r['price'] < by_source[src]['price']:
                by_source[src] = r
        return sorted(by_source.values(), key=lambda x: x['price'])

    # ── Single product fetch + DB persist ─────────────────────────────────────
    def fetch_and_save(self, product_id: int, url: str, name: str = '') -> dict | None:
        """
        Fetch current price for a tracked product and persist to DB.
        Tries: SerpAPI amazon_product → direct scraper → SerpAPI search.
        Returns result dict or None.
        """
        self._reload_key()
        result = None
        site   = _detect_site(url)

        # 1. SerpAPI amazon_product (best — gives ASIN-exact price)
        if 'amazon' in url.lower() and self.serpapi_key:
            asin = _extract_asin(url)
            if asin:
                result = _serpapi_amazon_product(asin, self.serpapi_key)

        # 2. Direct scraping
        if not result:
            if 'amazon.in' in url.lower():
                result = _scrape_amazon(url)
            elif 'flipkart.com' in url.lower():
                result = _scrape_flipkart(url)

        # 3. SerpAPI Google Shopping as last resort (uses query = product name)
        if not result and self.serpapi_key and name:
            hits = _serpapi_google_shopping(name, self.serpapi_key)
            # pick the cheapest hit from same platform
            for h in sorted(hits, key=lambda x: x['price']):
                if site.lower().split()[0] in h['source'].lower() or not result:
                    result = h
                    break

        if result and result.get('price'):
            _persist_price(product_id, result['price'], result.get('source', 'unknown'))
            return result

        print(f"❌ Could not fetch price for product_id={product_id}")
        return None

    # ── Bulk check (called by monitor) ────────────────────────────────────────
    def check_all(self) -> list[dict]:
        """
        Fetch & update prices for all active products in DB.
        Returns list of results.
        """
        with _get_db() as conn:
            products = conn.execute(
                'SELECT id, url, name FROM products WHERE active=1'
            ).fetchall()

        print(f"\n{'='*55}")
        print(f"🔄 Price check — {len(products)} products — {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*55}")

        results = []
        for p in products:
            print(f"\n📦 [{p['id']}] {p['name']}")
            r = self.fetch_and_save(p['id'], p['url'], p['name'])
            if r:
                results.append({'product_id': p['id'], 'name': p['name'], **r})
            time.sleep(2)   # be polite to APIs

        print(f"\n✅ Check complete — {len(results)}/{len(products)} updated")
        return results

    # ── Alert dispatch (called by monitor) ────────────────────────────────────
    def send_pending_alerts(self, mailer=None):
        """Send email alerts for any unsent alert rows."""
        if not mailer:
            return
        with _get_db() as conn:
            unsent = conn.execute(
                'SELECT a.*, p.name as product_name, p.url as product_url '
                'FROM alerts a JOIN products p ON a.product_id = p.id '
                'WHERE a.email_sent=0 ORDER BY a.sent_at DESC'
            ).fetchall()

        for alert in unsent:
            try:
                mailer.send_mail(
                    alert['product_url'],
                    alert['product_name'],
                    alert['new_price']
                )
                with _get_db() as conn:
                    conn.execute('UPDATE alerts SET email_sent=1 WHERE id=?', (alert['id'],))
                print(f"📧 Alert email sent for {alert['product_name']}")
            except Exception as e:
                print(f"❌ Failed to send alert email: {e}")


# Singleton so monitor and Flask app share one instance
fetcher = PriceFetcher()
