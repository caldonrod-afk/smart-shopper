# Smart Shopper

Track product prices, get alerts, and predict future prices with AI.

## Features

- Search products via Google Shopping (SerpAPI)
- Price history charts & AI predictions
- Email alerts for price drops
- Dark UI with side-by-side comparison
- Admin dashboard

## Quick Start

```bash
pip install flask requests beautifulsoup4 numpy google-search-results

cp .env.example .env
# Add your SerpAPI key (free: https://serpapi.com)

python app.py
# → http://127.0.0.1:5051
```

## Configuration

Set keys via `.env` file or Admin → Settings:
- `SERPAPI_KEY` - Google Shopping results (100 free/month)
- Gmail credentials - Price drop alerts

## Security

Never commit `config.json` or `.env` with real credentials. Add them to `.gitignore`.
