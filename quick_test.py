#!/usr/bin/env python3
"""Quick test of SerpAPI integration"""

print("🧪 Testing SerpAPI Integration...")
print("=" * 60)

# Test 1: Check API configuration
print("\n1️⃣ Checking API Configuration...")
try:
    from price_tracker.api_config import API_CONFIG, is_api_enabled
    
    serpapi_config = API_CONFIG.get('serpapi', {})
    api_key = serpapi_config.get('key', '')
    is_enabled = serpapi_config.get('enabled', False)
    
    print(f"   Enabled: {'✅ Yes' if is_enabled else '❌ No'}")
    print(f"   API Key: {'✅ Configured' if api_key else '❌ Missing'}")
    
    if is_enabled and api_key:
        print("   ✅ SerpAPI is ready!")
    else:
        print("   ❌ SerpAPI not configured properly")
        exit(1)
        
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# Test 2: Test API scraper
print("\n2️⃣ Testing API Scraper...")
try:
    from price_tracker.mailer import Mailer
    from price_tracker.api_scraper import APIScraper
    
    mailer = Mailer()
    scraper = APIScraper(mailer)
    print("   ✅ Scraper initialized")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# Test 3: Fetch real product data
print("\n3️⃣ Fetching Real Product Data...")
test_url = "https://www.amazon.in/dp/B0D1XD1ZV3"
print(f"   URL: {test_url}")

try:
    result = scraper.get_product_data(test_url)
    
    if result:
        print(f"\n   ✅ SUCCESS!")
        print(f"   📦 Product: {result['name']}")
        print(f"   💰 Price: ₹{result['price']:,.2f}")
        print(f"   💱 Currency: {result['currency']}")
        print(f"   📡 Source: {result['source']}")
    else:
        print("   ❌ Could not fetch product data")
        
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("🎉 Test Complete!")
print("\nNext steps:")
print("1. Run: python realtime_monitor.py")
print("2. Choose monitoring frequency")
print("3. Watch for price drops!")
print("=" * 60)
