#!/usr/bin/env python3
"""
Smart Shopper - Unified Flask Application
Single entry point replacing web_monitor.py + web_server.py
"""
import json
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for

# ── Real scraper (lazy import so app still starts if deps missing) ────────────
try:
    from price_tracker.scraper import fetcher as _fetcher
    SCRAPER_OK = True
except Exception as _e:
    print(f"⚠️  Scraper not loaded: {_e}")
    SCRAPER_OK = False
    _fetcher = None

# ── Config ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DB_PATH  = BASE_DIR / 'data' / 'price_tracker.db'
CFG_PATH = BASE_DIR / 'config.json'

DB_PATH.parent.mkdir(exist_ok=True)

app = Flask(
    __name__,
    template_folder='price_tracker/web/templates',
    static_folder='price_tracker/web/static'
)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')

# ── DB helpers ───────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with get_db() as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS products (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                url           TEXT UNIQUE NOT NULL,
                name          TEXT,
                image_url     TEXT,
                target_price  REAL NOT NULL,
                current_price REAL,
                lowest_price  REAL,
                highest_price REAL,
                website       TEXT,
                last_checked  TIMESTAMP,
                active        INTEGER DEFAULT 1,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS price_history (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                price      REAL NOT NULL,
                source     TEXT,
                timestamp  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS alerts (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                old_price  REAL,
                new_price  REAL,
                message    TEXT,
                email_sent INTEGER DEFAULT 0,
                sent_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_ph_product ON price_history(product_id, timestamp DESC);
        ''')
    print("✅ Database ready")

init_db()

# ── Config helpers ────────────────────────────────────────────────────────────
def load_config():
    try:
        if CFG_PATH.exists():
            return json.loads(CFG_PATH.read_text())
    except Exception:
        pass
    return {}

def save_config(data):
    CFG_PATH.write_text(json.dumps(data, indent=2))

# ── Pages ─────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/product/<int:pid>')
def product_detail(pid):
    with get_db() as conn:
        product = conn.execute('SELECT * FROM products WHERE id=?', (pid,)).fetchone()
    if not product:
        return redirect('/')
    return render_template('product.html', product=dict(product))

@app.route('/watchlist')
def watchlist():
    return render_template('watchlist.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

# ── REST API ──────────────────────────────────────────────────────────────────
@app.route('/api/products', methods=['GET'])
def api_get_products():
    with get_db() as conn:
        rows = conn.execute(
            'SELECT * FROM products WHERE active=1 ORDER BY created_at DESC'
        ).fetchall()
    products = []
    for r in rows:
        p = dict(r)
        # compute % change
        if p['current_price'] and p['highest_price']:
            p['drop_pct'] = round(
                (p['highest_price'] - p['current_price']) / p['highest_price'] * 100, 1
            )
        else:
            p['drop_pct'] = 0
        products.append(p)
    return jsonify({'success': True, 'products': products})

@app.route('/api/products', methods=['POST'])
def api_add_product():
    data = request.get_json() or {}
    url          = data.get('url', '').strip()
    name         = data.get('name', '').strip()
    target_price = data.get('target_price') or data.get('warn_price')
    image_url    = data.get('image_url', '')
    website      = data.get('website', _detect_site(url))

    if not url or not target_price:
        return jsonify({'success': False, 'error': 'URL and target price are required'}), 400

    try:
        target_price = float(target_price)
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid price'}), 400

    with get_db() as conn:
        try:
            conn.execute(
                'INSERT INTO products (url, name, image_url, target_price, website) VALUES (?,?,?,?,?)',
                (url, name or 'Unnamed Product', image_url, target_price, website)
            )
            pid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
            product = dict(conn.execute('SELECT * FROM products WHERE id=?', (pid,)).fetchone())
            return jsonify({'success': True, 'product': product}), 201
        except sqlite3.IntegrityError:
            return jsonify({'success': False, 'error': 'Product already being tracked'}), 409

@app.route('/api/products/<int:pid>', methods=['DELETE'])
def api_delete_product(pid):
    with get_db() as conn:
        conn.execute('UPDATE products SET active=0 WHERE id=?', (pid,))
    return jsonify({'success': True})

@app.route('/api/products/<int:pid>/history')
def api_price_history(pid):
    days = int(request.args.get('days', 30))
    since = datetime.now() - timedelta(days=days)
    with get_db() as conn:
        rows = conn.execute(
            'SELECT price, timestamp FROM price_history WHERE product_id=? AND timestamp>=? ORDER BY timestamp ASC',
            (pid, since)
        ).fetchall()
    history = [{'price': r['price'], 'timestamp': r['timestamp']} for r in rows]
    # If no history yet, create demo curve from current price
    if not history:
        with get_db() as conn:
            prod = conn.execute('SELECT current_price, target_price FROM products WHERE id=?', (pid,)).fetchone()
        if prod and prod['current_price']:
            import random
            base = prod['current_price']
            history = []
            for i in range(days, -1, -1):
                ts = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d %H:%M')
                noise = random.uniform(-0.03, 0.03)
                history.append({'price': round(base * (1 + noise + i*0.002), 2), 'timestamp': ts})
    return jsonify({'success': True, 'history': history})

@app.route('/api/products/<int:pid>/price', methods=['POST'])
def api_update_price(pid):
    """Manually update a product's current price (used by monitor)"""
    data  = request.get_json() or {}
    price = data.get('price')
    if not price:
        return jsonify({'success': False, 'error': 'price required'}), 400
    price = float(price)

    with get_db() as conn:
        prod = conn.execute('SELECT * FROM products WHERE id=?', (pid,)).fetchone()
        if not prod:
            return jsonify({'success': False, 'error': 'Not found'}), 404
        prod = dict(prod)

        low  = min(price, prod['lowest_price'])  if prod['lowest_price']  else price
        high = max(price, prod['highest_price']) if prod['highest_price'] else price

        conn.execute(
            'UPDATE products SET current_price=?, lowest_price=?, highest_price=?, last_checked=CURRENT_TIMESTAMP WHERE id=?',
            (price, low, high, pid)
        )
        conn.execute(
            'INSERT INTO price_history (product_id, price, source) VALUES (?,?,?)',
            (pid, price, data.get('source', 'manual'))
        )

        if price <= prod['target_price']:
            conn.execute(
                'INSERT INTO alerts (product_id, old_price, new_price, message) VALUES (?,?,?,?)',
                (pid, prod['current_price'], price,
                 f"Price dropped to ₹{price:,.0f} — below your alert of ₹{prod['target_price']:,.0f}")
            )

    return jsonify({'success': True})

@app.route('/api/search')
def api_search():
    """Search products via SerpAPI Google Shopping (real data)."""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'success': False, 'error': 'Query required'}), 400

    if SCRAPER_OK:
        try:
            results = _fetcher.search(query)
            if results:
                # normalise to include price_str
                for r in results:
                    r['price_str'] = '₹' + f"{r['price']:,.0f}"
                return jsonify({'success': True, 'results': results})
        except Exception as e:
            print(f"Scraper search error: {e}")

    # Fallback demo
    return jsonify({'success': True, 'results': _demo_search_results(query), 'demo': True})


@app.route('/api/compare')
def api_compare():
    """Best price per source for a query (real data)."""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'success': False, 'error': 'Query required'}), 400

    if SCRAPER_OK:
        try:
            comparisons = _fetcher.compare(query)
            if comparisons:
                for c in comparisons:
                    c['price_str'] = '₹' + f"{c['price']:,.0f}"
                return jsonify({'success': True, 'comparisons': comparisons})
        except Exception as e:
            print(f"Scraper compare error: {e}")

    return jsonify({'success': True, 'comparisons': _demo_compare(query), 'demo': True})


@app.route('/api/products/<int:pid>/refresh', methods=['POST'])
def api_refresh_product(pid):
    """Manually trigger a price fetch for one product (used by UI Refresh button)."""
    if not SCRAPER_OK:
        return jsonify({'success': False, 'error': 'Scraper not available'}), 503

    with get_db() as conn:
        prod = conn.execute('SELECT * FROM products WHERE id=?', (pid,)).fetchone()
    if not prod:
        return jsonify({'success': False, 'error': 'Product not found'}), 404

    result = _fetcher.fetch_and_save(pid, prod['url'], prod['name'])
    if result:
        return jsonify({'success': True, 'price': result['price'], 'source': result.get('source')})
    return jsonify({'success': False, 'error': 'Could not fetch price — check SerpAPI key or URL'}), 502

@app.route('/api/dashboard')
def api_dashboard():
    with get_db() as conn:
        total     = conn.execute('SELECT COUNT(*) FROM products WHERE active=1').fetchone()[0]
        drops     = conn.execute(
            'SELECT COUNT(*) FROM products WHERE active=1 AND current_price IS NOT NULL AND current_price <= target_price'
        ).fetchone()[0]
        alerts    = conn.execute(
            "SELECT COUNT(*) FROM alerts WHERE sent_at >= datetime('now','-7 days')"
        ).fetchone()[0]
        tracking  = conn.execute('SELECT COUNT(*) FROM products WHERE active=1').fetchone()[0]
    return jsonify({
        'success': True,
        'stats': {
            'total_products': total,
            'price_drops':    drops,
            'recent_alerts':  alerts,
            'tracking':       tracking
        }
    })

@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    if request.method == 'GET':
        cfg = load_config()
        # Never expose password
        safe = {k: v for k, v in cfg.items() if 'password' not in k.lower()}
        return jsonify({'success': True, 'config': safe})
    data = request.get_json() or {}
    cfg  = load_config()
    cfg.update(data)
    save_config(cfg)
    return jsonify({'success': True})

@app.route('/api/alerts')
def api_alerts():
    with get_db() as conn:
        rows = conn.execute('''
            SELECT a.*, p.name as product_name, p.url as product_url
            FROM alerts a JOIN products p ON a.product_id = p.id
            ORDER BY a.sent_at DESC LIMIT 50
        ''').fetchall()
    return jsonify({'success': True, 'alerts': [dict(r) for r in rows]})

# ── Prediction ────────────────────────────────────────────────────────────────
@app.route('/api/products/<int:pid>/predict')
def api_predict(pid):
    """Linear-regression price prediction over stored history."""
    with get_db() as conn:
        rows = conn.execute(
            'SELECT price FROM price_history WHERE product_id=? ORDER BY timestamp ASC',
            (pid,)
        ).fetchall()

    if len(rows) < 5:
        return jsonify({'success': False, 'error': 'Need at least 5 price records for prediction. Keep tracking!'})

    try:
        import numpy as np
        prices = [r['price'] for r in rows]
        x      = np.arange(len(prices), dtype=float)
        slope, intercept = np.polyfit(x, prices, 1)

        last     = prices[-1]
        pred7    = round(float(intercept + slope * (len(prices) + 7)), 2)
        trend    = 'dropping' if slope < -10 else ('rising' if slope > 10 else 'stable')
        chg_pct  = round(abs(slope * 7) / last * 100, 1)
        confidence = min(92, max(45, 50 + len(rows)))

        return jsonify({
            'success':      True,
            'trend':        trend,
            'slope':        round(float(slope), 2),
            'current':      last,
            'predicted_7d': pred7,
            'change_pct':   chg_pct,
            'confidence':   confidence,
            'data_points':  len(rows),
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/monitor/status')
def api_monitor_status():
    """Check if monitor.py is keeping prices fresh."""
    with get_db() as conn:
        # Count products checked in last 10 minutes
        recent = conn.execute(
            "SELECT COUNT(*) FROM products WHERE last_checked >= datetime('now','-10 minutes')"
        ).fetchone()[0]
        oldest = conn.execute(
            "SELECT MIN(last_checked) FROM products WHERE active=1"
        ).fetchone()[0]
    return jsonify({
        'success': True,
        'recent_checks': recent,
        'oldest_check':  oldest,
        'scraper_ready': SCRAPER_OK,
    })


# ── Helpers ───────────────────────────────────────────────────────────────────
def _detect_site(url):
    url = url.lower()
    if 'amazon'   in url: return 'Amazon India'
    if 'flipkart' in url: return 'Flipkart'
    if 'meesho'   in url: return 'Meesho'
    if 'myntra'   in url: return 'Myntra'
    if 'snapdeal' in url: return 'Snapdeal'
    return 'Other'

def _demo_search_results(query):
    """Fallback demo data when SerpAPI key is missing"""
    return [
        {'title': f'{query} - 128GB Black', 'price': 54999, 'price_str': '₹54,999',
         'source': 'Amazon India', 'link': '#', 'image': '', 'rating': 4.5, 'reviews': 2840},
        {'title': f'{query} - 256GB Blue',  'price': 62999, 'price_str': '₹62,999',
         'source': 'Flipkart',    'link': '#', 'image': '', 'rating': 4.3, 'reviews': 1920},
        {'title': f'{query} - 128GB White', 'price': 56500, 'price_str': '₹56,500',
         'source': 'Meesho',      'link': '#', 'image': '', 'rating': 4.1, 'reviews': 880},
    ]

def _demo_compare(query):
    return [
        {'source': 'Amazon India', 'price': 54999, 'title': f'{query} - Best Deal', 'link': '#', 'image': '', 'rating': 4.5, 'reviews': 2840},
        {'source': 'Flipkart',     'price': 57490, 'title': f'{query}',             'link': '#', 'image': '', 'rating': 4.3, 'reviews': 1920},
        {'source': 'Meesho',       'price': 58000, 'title': f'{query}',             'link': '#', 'image': '', 'rating': 4.1, 'reviews': 650},
    ]

if __name__ == '__main__':
    print("🛍️  Smart Shopper starting on http://127.0.0.1:5051")
    app.run(host='127.0.0.1', port=5051, debug=True)
