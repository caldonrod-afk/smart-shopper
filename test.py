#!/usr/bin/env python3
"""
Smart Shopper — API Key Tester
Run: python test.py
"""
import json
import sys
import time
from pathlib import Path

# ── Load config ───────────────────────────────────────────────────────────────
CFG_PATH = Path(__file__).parent / 'config.json'

def load_config():
    try:
        return json.loads(CFG_PATH.read_text())
    except FileNotFoundError:
        print("❌ config.json not found! Create it in the project root.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ config.json is invalid JSON: {e}")
        sys.exit(1)

# ── Helpers ───────────────────────────────────────────────────────────────────
def section(title):
    print(f"\n{'─'*50}")
    print(f"  {title}")
    print(f"{'─'*50}")

def ok(msg):   print(f"  ✅  {msg}")
def fail(msg): print(f"  ❌  {msg}")
def warn(msg): print(f"  ⚠️   {msg}")
def info(msg): print(f"  ℹ️   {msg}")

# ── Test 1: config.json ───────────────────────────────────────────────────────
def test_config(cfg):
    section("1. config.json")

    serpapi_key = cfg.get('serpapi_key', '').strip()
    gemini_key  = cfg.get('gemini_api_key', '').strip()

    if not serpapi_key or serpapi_key == 'YOUR_SERPAPI_KEY_HERE':
        fail("serpapi_key is missing or still a placeholder")
    else:
        ok(f"serpapi_key found  ({serpapi_key[:6]}...{serpapi_key[-4:]})")

    if not gemini_key or gemini_key == 'YOUR_GEMINI_API_KEY_HERE':
        fail("gemini_api_key is missing or still a placeholder")
    else:
        ok(f"gemini_api_key found  ({gemini_key[:6]}...{gemini_key[-4:]})")

    return serpapi_key, gemini_key

# ── Test 2: SerpAPI ───────────────────────────────────────────────────────────
def test_serpapi(key):
    section("2. SerpAPI — Google Shopping")

    if not key or key == 'YOUR_SERPAPI_KEY_HERE':
        warn("Skipping — no key provided")
        return

    import requests
    try:
        info("Sending test search for 'OnePlus 13' ...")
        resp = requests.get(
            'https://serpapi.com/search',
            params={
                'engine':  'google_shopping',
                'q':       'OnePlus 13 India',
                'gl':      'in',
                'hl':      'en',
                'api_key': key,
                'num':     3,
            },
            timeout=20,
        )

        if resp.status_code == 401:
            fail(f"401 Unauthorized — API key is INVALID or expired")
            info("→ Go to https://serpapi.com/manage-api-key and copy your key again")
            return

        if resp.status_code == 429:
            fail("429 Too Many Requests — you've hit the monthly limit (100 searches/month on free tier)")
            info("→ Upgrade at serpapi.com or wait until next month")
            return

        resp.raise_for_status()
        data = resp.json()

        if 'error' in data:
            fail(f"SerpAPI error: {data['error']}")
            return

        results = data.get('shopping_results', [])
        if results:
            ok(f"Got {len(results)} results!")
            for r in results[:3]:
                price = r.get('extracted_price') or r.get('price', 'N/A')
                print(f"      • {r.get('title','')[:55]:<55}  ₹{price}  ({r.get('source','')})")
        else:
            warn("Search succeeded but returned 0 shopping results")
            info("→ The key works, but try a different query")

        # Show account info if available
        meta = data.get('search_metadata', {})
        info(f"Plan status: {meta.get('status', 'unknown')}")

    except requests.exceptions.ConnectionError:
        fail("Could not reach serpapi.com — check your internet connection")
    except Exception as e:
        fail(f"Unexpected error: {e}")

# ── Test 3: Gemini ────────────────────────────────────────────────────────────
def test_gemini(key):
    section("3. Gemini API — gemini-2.0-flash-lite")

    if not key or key == 'YOUR_GEMINI_API_KEY_HERE':
        warn("Skipping — no key provided")
        return

    import requests

    models_to_try = [
    'gemini-2.5-flash-lite',  # Newest high-throughput model
    'gemini-2.5-flash',       # Current standard flash model
    'gemini-2.0-flash-lite',  # Use only if still supported in your region
    'gemini-2.0-flash',       # Use only if still supported in your region
     ]

    for model in models_to_try:
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}'
        info(f"Testing model: {model} ...")
        try:
            resp = requests.post(
                url,
                json={
                    'contents': [{'role': 'user', 'parts': [{'text': 'Reply with exactly: OK'}]}],
                    'generationConfig': {'maxOutputTokens': 10},
                },
                timeout=15,
            )

            if resp.status_code == 400:
                data = resp.json()
                fail(f"400 Bad Request: {data.get('error', {}).get('message', 'unknown')}")
                continue

            if resp.status_code == 401 or resp.status_code == 403:
                fail(f"{resp.status_code} — API key is INVALID or lacks Gemini API access")
                info("→ Go to https://aistudio.google.com/app/apikey and create/copy a new key")
                info("→ Make sure the Generative Language API is enabled in your Google Cloud project")
                return  # no point trying other models with a bad key

            if resp.status_code == 429:
                warn(f"429 Rate limit hit on {model}")
                info("→ Waiting 5 seconds before trying next model...")
                time.sleep(5)
                continue

            if resp.status_code == 404:
                warn(f"Model {model} not found — trying next...")
                continue

            resp.raise_for_status()
            reply = resp.json()['candidates'][0]['content']['parts'][0]['text'].strip()
            ok(f"Model '{model}' works! Response: '{reply}'")
            info(f"→ Update GEMINI_API_URL in app.py to use: {model}")
            return

        except requests.exceptions.ConnectionError:
            fail("Could not reach generativelanguage.googleapis.com — check internet connection")
            return
        except Exception as e:
            fail(f"Unexpected error with {model}: {e}")

    fail("All Gemini models failed or rate-limited")
    info("→ Wait a minute and run this test again")
    info("→ Or check https://aistudio.google.com for quota details")

# ── Test 4: Flask app (optional) ──────────────────────────────────────────────
def test_flask():
    section("4. Flask app — http://127.0.0.1:5051")
    import requests
    try:
        resp = requests.get('http://127.0.0.1:5051/api/dashboard', timeout=5)
        if resp.status_code == 200:
            ok("App is running and /api/dashboard responded OK")
        else:
            warn(f"App responded with status {resp.status_code}")
    except requests.exceptions.ConnectionError:
        warn("App is not running (start it with: python app.py)")

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("\n🛍️  Smart Shopper — API Key Tester")

    cfg = load_config()
    serpapi_key, gemini_key = test_config(cfg)
    test_serpapi(serpapi_key)
    test_gemini(gemini_key)
    test_flask()

    print(f"\n{'─'*50}")
    print("  Done. Fix any ❌ above, then re-run to confirm.")
    print(f"{'─'*50}\n")