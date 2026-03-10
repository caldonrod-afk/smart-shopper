# Smart Shopper — Upgraded

## What's new
- Single Flask app (`app.py`) replaces `web_monitor.py` + `web_server.py` + `admin_monitor.py`
- Full dark UI: search, side-by-side compare table, price history chart, AI prediction
- REST API (`/api/*`) for all data operations
- Price history chart (Chart.js) on every product page
- AI price prediction via linear regression on stored history
- Admin dashboard with settings, all products, alert history
- Secrets moved out of code — use `.env` or the Admin settings page

## Setup

```bash
pip install flask requests beautifulsoup4 numpy google-search-results

# Copy and fill in your keys
cp .env.example .env

python app.py
# → http://127.0.0.1:5051
```

## Getting prices (SerpAPI)

1. Sign up at https://serpapi.com (100 free searches/month)
2. Go to Admin → Settings → paste your SerpAPI key → Save
3. Search for any product — live Google Shopping results will appear

Without a SerpAPI key, the app runs with demo data so you can still see the full UI.

## Background monitoring

The existing `api_monitor.py` / `realtime_monitor.py` still work unchanged.
They call `POST /api/products/<id>/price` to update prices in the DB,
which the new UI reads automatically.

## ⚠️ Security fix
The Gmail password in `config.json` was committed to GitHub.
- Go to Google Account → Security → App Passwords → revoke the old one
- Enter a new one in Admin → Settings (stored only in `config.json`, never hardcoded)
- Add `config.json` to `.gitignore` or use the `.env` file instead
