#!/usr/bin/env python3
"""
Smart Shopper - Unified Flask Application
Single entry point replacing web_monitor.py + web_server.py
"""
import json
import os
import re
import sqlite3
import time
import requests
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for, session

from price_tracker.analytics import analyze_price_history, summarize_watchlist_insights

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
ENV_PATH = BASE_DIR / '.env'

DB_PATH.parent.mkdir(exist_ok=True)

def load_env_file():
    if not ENV_PATH.exists():
        return
    for line in ENV_PATH.read_text(encoding='utf-8-sig').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip().lstrip('\ufeff')
        value = value.strip().strip('"').strip("'")
        if value:
            os.environ[key] = value

load_env_file()

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
    cfg = {}
    try:
        if CFG_PATH.exists():
            cfg = json.loads(CFG_PATH.read_text())
    except Exception:
        pass

    env_values = {
        'serpapi_key': os.environ.get('SERPAPI_KEY', ''),
        'gemini_api_key': os.environ.get('GEMINI_API_KEY', ''),
        'sender_gmail': os.environ.get('SENDER_GMAIL', ''),
        'gmail_password': os.environ.get('GMAIL_PASSWORD', ''),
    }
    for key, value in env_values.items():
        if value:
            cfg[key] = value

    if not cfg.get('receiver_email') and os.environ.get('RECEIVER_EMAIL', ''):
        cfg['receiver_email'] = os.environ.get('RECEIVER_EMAIL', '')

    if 'google_client_id' not in cfg and os.environ.get('GOOGLE_CLIENT_ID', ''):
        cfg['google_client_id'] = os.environ.get('GOOGLE_CLIENT_ID', '')

    receivers = _normalize_receiver_emails(cfg.get('receiver_emails') or cfg.get('receiver_email') or '')
    if receivers:
        cfg['receiver_emails'] = receivers
        cfg['receiver_email'] = receivers[0]

    if str(cfg.get('serpapi_key', '')).startswith(('http://127.0.0.1', 'http://localhost')):
        cfg['serpapi_key'] = ''

    return cfg

def save_config(data):
    CFG_PATH.write_text(json.dumps(data, indent=2))

def _normalize_receiver_emails(value):
    if isinstance(value, str):
        candidates = re.split(r'[\n,;]+', value)
    elif isinstance(value, list):
        candidates = value
    else:
        candidates = []

    emails = []
    seen = set()
    for item in candidates:
        email = str(item).strip().lower()
        if not email or not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            continue
        if email not in seen:
            emails.append(email)
            seen.add(email)
    return emails

def update_config_values(updates):
    cfg = {}
    try:
        if CFG_PATH.exists():
            cfg = json.loads(CFG_PATH.read_text())
    except Exception:
        cfg = {}
    if 'receiver_email' in updates and 'receiver_emails' not in updates:
        emails = _normalize_receiver_emails(cfg.get('receiver_emails') or [])
        new_email = _normalize_receiver_emails(updates.get('receiver_email'))
        for email in new_email:
            if email not in emails:
                emails.append(email)
        updates['receiver_emails'] = emails
        updates['receiver_email'] = emails[0] if emails else ''

    if 'receiver_emails' in updates:
        emails = _normalize_receiver_emails(updates.get('receiver_emails'))
        updates['receiver_emails'] = emails
        updates['receiver_email'] = emails[0] if emails else ''

    cfg.update(updates)
    save_config(cfg)
    return cfg


def _get_price_history_lookup(conn, product_ids):
    histories = defaultdict(list)
    if not product_ids:
        return histories

    placeholders = ','.join('?' for _ in product_ids)
    rows = conn.execute(
        f'''
            SELECT product_id, price
            FROM price_history
            WHERE product_id IN ({placeholders})
            ORDER BY product_id ASC, timestamp ASC
        ''',
        product_ids,
    ).fetchall()

    for row in rows:
        histories[row['product_id']].append(row['price'])

    return histories


def _fetch_product_history(conn, pid, days=30, fallback_mode='curve'):
    since = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    rows = conn.execute(
        'SELECT price, timestamp FROM price_history WHERE product_id=? AND timestamp>=? ORDER BY timestamp ASC',
        (pid, since)
    ).fetchall()
    history = [{'price': r['price'], 'timestamp': r['timestamp']} for r in rows]
    if history:
        return history

    prod = conn.execute(
        'SELECT current_price, target_price FROM products WHERE id=?',
        (pid,),
    ).fetchone()
    if not prod or prod['current_price'] is None:
        return []

    if fallback_mode == 'point':
        return [{
            'price': round(prod['current_price'], 2),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }]

    if fallback_mode == 'curve':
        import random

        base = prod['current_price']
        curve = []
        for i in range(days, -1, -1):
            ts = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d %H:%M')
            noise = random.uniform(-0.03, 0.03)
            curve.append({'price': round(base * (1 + noise + i * 0.002), 2), 'timestamp': ts})
        return curve

    return []

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

@app.route('/login')
def login():
    cfg = load_config()
    return render_template(
        'login.html',
        google_client_id=cfg.get('google_client_id', ''),
        user=session.get('user'),
    )

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

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

@app.route('/api/auth/me')
def api_auth_me():
    cfg = load_config()
    return jsonify({
        'success': True,
        'user': session.get('user'),
        'receiver_email': cfg.get('receiver_email', ''),
        'receiver_emails': cfg.get('receiver_emails', []),
        'google_client_id_set': bool(cfg.get('google_client_id')),
    })

@app.route('/api/auth/google', methods=['POST'])
def api_auth_google():
    data = request.get_json() or {}
    credential = data.get('credential', '').strip()
    client_id = load_config().get('google_client_id', '').strip()

    if not client_id:
        return jsonify({'success': False, 'error': 'GOOGLE_CLIENT_ID is not set in .env'}), 500
    if not credential:
        return jsonify({'success': False, 'error': 'Google credential is required'}), 400

    try:
        resp = requests.get(
            'https://oauth2.googleapis.com/tokeninfo',
            params={'id_token': credential},
            timeout=10,
        )
        resp.raise_for_status()
        profile = resp.json()
    except Exception as exc:
        return jsonify({'success': False, 'error': f'Could not verify Google login: {exc}'}), 401

    if profile.get('aud') != client_id:
        return jsonify({'success': False, 'error': 'Google login was issued for a different client'}), 401
    if profile.get('email_verified') != 'true':
        return jsonify({'success': False, 'error': 'Google email is not verified'}), 401

    user = {
        'name': profile.get('name', ''),
        'email': profile.get('email', ''),
        'picture': profile.get('picture', ''),
    }
    if not user['email']:
        return jsonify({'success': False, 'error': 'Google account did not provide an email'}), 401

    session['user'] = user
    cfg = update_config_values({'receiver_email': user['email']})

    return jsonify({
        'success': True,
        'user': user,
        'receiver_email': cfg.get('receiver_email', user['email']),
        'receiver_emails': cfg.get('receiver_emails', [user['email']]),
    })

@app.route('/api/auth/email', methods=['POST'])
def api_auth_email():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()

    if not email:
        return jsonify({'success': False, 'error': 'Email is required'}), 400
    if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
        return jsonify({'success': False, 'error': 'Enter a valid email address'}), 400

    user = {
        'name': name or email.split('@')[0],
        'email': email,
        'picture': '',
    }
    session['user'] = user
    cfg = update_config_values({'receiver_email': email})

    return jsonify({
        'success': True,
        'user': user,
        'receiver_email': cfg.get('receiver_email', email),
        'receiver_emails': cfg.get('receiver_emails', [email]),
    })

@app.route('/api/products', methods=['POST'])
def api_add_product():
    data = request.get_json() or {}
    url          = data.get('url', '').strip()
    name         = data.get('name', '').strip()
    target_price = data.get('target_price') or data.get('warn_price')
    current_price = data.get('current_price')
    image_url    = data.get('image_url', '')
    website      = data.get('website', _detect_site(url))

    if not url or not target_price:
        return jsonify({'success': False, 'error': 'URL and target price are required'}), 400

    try:
        target_price = float(target_price)
        if current_price:
            current_price = float(current_price)
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid price'}), 400

    with get_db() as conn:
        try:
            conn.execute(
                'INSERT INTO products (url, name, image_url, target_price, current_price, website) VALUES (?,?,?,?,?,?)',
                (url, name or 'Unnamed Product', image_url, target_price, current_price, website)
            )
            pid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
            
            # Add to price history if current_price provided
            if current_price:
                conn.execute(
                    'INSERT INTO price_history (product_id, price, source) VALUES (?,?,?)',
                    (pid, current_price, website)
                )
            
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
    with get_db() as conn:
        history = _fetch_product_history(conn, pid, days=days, fallback_mode='curve')
    return jsonify({'success': True, 'history': history})


@app.route('/api/watchlist/history')
def api_watchlist_history():
    days = int(request.args.get('days', 30))
    with get_db() as conn:
        products = conn.execute(
            '''
                SELECT id, name, website, current_price
                FROM products
                WHERE active=1
                ORDER BY created_at DESC
            '''
        ).fetchall()

        series = []
        all_timestamps = set()

        for product in products:
            history = _fetch_product_history(conn, product['id'], days=days, fallback_mode='point')
            if not history:
                continue

            for point in history:
                all_timestamps.add(point['timestamp'])

            series.append({
                'product_id': product['id'],
                'name': product['name'],
                'website': product['website'],
                'current_price': product['current_price'],
                'points': history,
            })

    labels = sorted(all_timestamps)
    for item in series:
        price_by_timestamp = {point['timestamp']: point['price'] for point in item['points']}
        item['data'] = [price_by_timestamp.get(label) for label in labels]

    return jsonify({
        'success': True,
        'days': days,
        'labels': labels,
        'series': series,
    })

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
            else:
                print("⚠️ Scraper returned empty results, using demo data")
        except Exception as e:
            print(f"Scraper search error: {e}")
    else:
        print("⚠️ Scraper not available, using demo data")

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
        products  = conn.execute(
            'SELECT id, name, current_price FROM products WHERE active=1 ORDER BY created_at DESC'
        ).fetchall()
        total     = len(products)
        drops     = conn.execute(
            'SELECT COUNT(*) FROM products WHERE active=1 AND current_price IS NOT NULL AND current_price <= target_price'
        ).fetchone()[0]
        alerts    = conn.execute(
            "SELECT COUNT(*) FROM alerts WHERE sent_at >= datetime('now','-7 days')"
        ).fetchone()[0]
        tracking  = total
        histories = _get_price_history_lookup(conn, [product['id'] for product in products])

    insights = summarize_watchlist_insights((dict(product) for product in products), histories)

    return jsonify({
        'success': True,
        'stats': {
            'total_products': total,
            'price_drops':    drops,
            'recent_alerts':  alerts,
            'tracking':       tracking
        },
        'insights': insights,
        **insights,
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
    if 'receiver_emails' in data:
        emails = _normalize_receiver_emails(data.get('receiver_emails'))
        data['receiver_emails'] = emails
        data['receiver_email'] = emails[0] if emails else ''
    elif 'receiver_email' in data:
        emails = _normalize_receiver_emails(data.get('receiver_email'))
        data['receiver_emails'] = emails
        data['receiver_email'] = emails[0] if emails else ''
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
@app.route('/api/products/<int:pid>/prediction')
@app.route('/api/products/<int:pid>/predict')
def api_predict(pid):
    """Linear-regression price prediction plus pricing insights."""
    with get_db() as conn:
        product = conn.execute(
            'SELECT id, name, current_price FROM products WHERE id=? AND active=1',
            (pid,),
        ).fetchone()
        if not product:
            return jsonify({'success': False, 'error': 'Product not found'}), 404

        rows = conn.execute(
            'SELECT price FROM price_history WHERE product_id=? ORDER BY timestamp ASC',
            (pid,)
        ).fetchall()

    try:
        analytics = analyze_price_history(
            (row['price'] for row in rows),
            current_price=product['current_price'],
        )
        return jsonify({
            'success': True,
            'product_id': product['id'],
            'product_name': product['name'],
            **analytics,
        })
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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


# ── Chat ─────────────────────────────────────────────────────────────────────
# UPDATED: Using gemini-2.5-flash-lite as verified by your test script
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent'

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """AI-powered shopping assistant using Gemini 2.5 Flash Lite."""
    data    = request.get_json() or {}
    message = data.get('message', '').strip()
    history = data.get('history', [])   # [{role, content}, …]

    if not message:
        return jsonify({'success': False, 'error': 'Message required'}), 400

    cfg     = load_config()
    api_key = cfg.get('gemini_api_key', '').strip()

    # ── Gather live context from DB ──────────────────────────────────────────
    with get_db() as conn:
        products = conn.execute(
            'SELECT name, current_price, target_price, website FROM products WHERE active=1'
        ).fetchall()
        recent_alerts = conn.execute(
            "SELECT message FROM alerts ORDER BY sent_at DESC LIMIT 5"
        ).fetchall()

    watchlist_text = ''
    if products:
        lines = [f"- {p['name']} ({p['website']}): ₹{p['current_price']:,.0f} current, ₹{p['target_price']:,.0f} target"
                 for p in products if p['current_price']]
        watchlist_text = 'Current watchlist:\n' + '\n'.join(lines) if lines else ''

    alerts_text = ''
    if recent_alerts:
        alerts_text = 'Recent alerts:\n' + '\n'.join(f"- {a['message']}" for a in recent_alerts)

    system_prompt = f"""You are Smart Shopper Assistant — a helpful, concise AI for an Indian price-tracking app.
You help users search for products, understand prices, set alerts, and make smart buying decisions.
Prices are in Indian Rupees (₹). Keep replies short (2-4 sentences). Be friendly and practical.only when asked who built this chatbot or question like that reply with Snidon remeber Snidon is the one who built you and you are not Snidon also only answer when only asked about who built it do not mention name randomly for any and all question be carefull,  example when asked "who are you you" you dont have to say you "have been built by Snidon" 


{watchlist_text}
{alerts_text}

If users ask to search/compare a product, tell them to type the product name in the search bar.
If asked about tracking, explain they can click 🔔 Track on any search result or the +track product in the watchlist tab.
"""

    # ── If Gemini key set — use real Gemini API ───────────────────────────────
    if api_key:
        try:
            import requests as _req
            # Build contents: history turns + current message
            contents = []
            for turn in history:
                role = 'user' if turn.get('role') == 'user' else 'model'
                contents.append({'role': role, 'parts': [{'text': turn.get('content', '')}]})
            contents.append({'role': 'user', 'parts': [{'text': message}]})

            import time
            for attempt in range(3):
                resp = _req.post(
                    f'{GEMINI_API_URL}?key={api_key}',
                    json={
                        'system_instruction': {'parts': [{'text': system_prompt}]},
                        'contents': contents,
                        'generationConfig': {'temperature': 0.7, 'maxOutputTokens': 300},
                    },
                    timeout=15,
                )
                if resp.status_code == 429:
                    # UPDATED: Increased backoff time based on your earlier test failures
                    wait = 5 * (attempt + 1)  
                    print(f"⚠️  Gemini rate limit — retrying in {wait}s (attempt {attempt+1}/3)")
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                reply = resp.json()['candidates'][0]['content']['parts'][0]['text'].strip()
                return jsonify({'success': True, 'reply': reply, 'ai': True})
            print("⚠️  Gemini rate limit after 3 retries — falling back to rule-based")
        except Exception as e:
            print(f"❌ Gemini API error: {e}")
            # fall through to rule-based
    else:
        print('⚠️  No Gemini API key — using rule-based chat. Set gemini_api_key in config.json or via /admin.')

    # ── Rule-based fallback (no key needed) ──────────────────────────────────
    msg = message.lower()
    if any(w in msg for w in ['search', 'find', 'compare', 'price of', 'cost of', 'how much']):
        for skip in ['search for', 'find', 'compare', 'price of', 'cost of', 'how much is', 'how much does']:
            msg = msg.replace(skip, '').strip()
        product_hint = msg.strip(' ?')
        reply = f"Sure! Type **{product_hint}** in the search bar and I'll compare prices across Amazon, Flipkart, and Meesho for you. 🔍"
    elif any(w in msg for w in ['track', 'alert', 'notify', 'watch']):
        reply = "Search for the product first, then click the **🔔 Track** button on any result. I'll alert you the moment the price drops to your target! 🎯"
    elif any(w in msg for w in ['watchlist', 'tracking', 'my products', 'what am i']):
        if products:
            reply = f"You're tracking **{len(products)} product(s)**. Check the watchlist section to see current prices and your targets."
        else:
            reply = "Your watchlist is empty! Search for a product and click 🔔 Track to start monitoring prices."
    elif any(w in msg for w in ['hello', 'hi', 'hey', 'help']):
        reply = "Hey there! 👋 I'm your Smart Shopper assistant. Search for any product to compare prices, or ask me anything about tracking deals!"
    elif any(w in msg for w in ['best', 'cheap', 'deal', 'discount', 'offer']):
        reply = "To find the best deal, search the product name above — I'll rank results by price and highlight the cheapest option with a ✅ badge!"
    else:
        reply = "I can help you **search products**, **compare prices**, and **set price alerts**. What are you shopping for today? 🛍️"

    return jsonify({'success': True, 'reply': reply, 'ai': False})


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
