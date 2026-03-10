#!/usr/bin/env python3
"""
Test script for SerpAPI integration
"""
import sys
from price_tracker.mailer import Mailer
from price_tracker.api_scraper import APIScraper

def test_serpapi():
    """Test SerpAPI with real Amazon India products"""
    print("🧪 Testing SerpAPI Integration")
    print("=" * 60)
    
    # Initialize components
    mailer = Mailer()
    scraper = APIScraper(mailer)
    
    # Test products from Amazon India
    test_products = [
        {
            'url': 'https://amzn.in/d/03nqyYdJ',
            'name': 'Samsung S25 Ultra',
            'warn_price': 139999.0
        },
        {
            'url': 'https://www.amazon.in/dp/B0D1XD1ZV3',
            'name': 'Apple iPhone 15 (128 GB) - Black',
            'warn_price': 70000.0
        },
        {
            'url': 'https://amzn.in/d/04GgrGKB',
            'name': 'Samsung Galaxy S25  5G',
            'warn_price': 13999
        }
    ]
    
    print("\n📋 Testing with real Amazon India products:")
    print("-" * 60)
    
    for i, product in enumerate(test_products, 1):
        print(f"\n🔍 Test {i}/{len(test_products)}")
        print(f"📦 Product: {product['name']}")
        print(f"🔗 URL: {product['url']}")
        print(f"💰 Alert Price: ₹{product['warn_price']:,.2f}")
        print("-" * 60)
        
        try:
            # Get product data
            result = scraper.get_product_data(product['url'])
            
            if result:
                print(f"\n✅ Successfully fetched product data!")
                print(f"📦 Product Name: {result['name']}")
                print(f"💰 Current Price: ₹{result['price']:,.2f}")
                print(f"💱 Currency: {result['currency']}")
                print(f"📡 Data Source: {result['source']}")
                
                if 'rating' in result and result['rating']:
                    print(f"⭐ Rating: {result['rating']}")
                if 'reviews_count' in result and result['reviews_count']:
                    print(f"📝 Reviews: {result['reviews_count']}")
                if 'availability' in result and result['availability']:
                    print(f"📦 Availability: {result['availability']}")
                
                # Check if price alert should trigger
                if result['price'] < product['warn_price']:
                    print(f"\n🚨 PRICE ALERT: Price is below threshold!")
                    print(f"   Current: ₹{result['price']:,.2f}")
                    print(f"   Threshold: ₹{product['warn_price']:,.2f}")
                    print(f"   Savings: ₹{product['warn_price'] - result['price']:,.2f}")
                else:
                    print(f"\n💰 Price is above threshold")
                    print(f"   Current: ₹{result['price']:,.2f}")
                    print(f"   Threshold: ₹{product['warn_price']:,.2f}")
                    print(f"   Difference: ₹{result['price'] - product['warn_price']:,.2f}")
            else:
                print(f"\n❌ Failed to fetch product data")
                print(f"   All API methods failed for this product")
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
        
        print("=" * 60)
    
    print("\n🎉 SerpAPI test completed!")
    print("\n💡 SETUP INSTRUCTIONS:")
    print("-" * 60)
    print("1. Sign up at: https://serpapi.com/")
    print("2. Get your API key from dashboard")
    print("3. Set environment variable:")
    print("   export SERPAPI_KEY='your_api_key_here'")
    print("   OR")
    print("   Edit price_tracker/api_config.py and add your key")
    print("-" * 60)

def check_serpapi_config():
    """Check if SerpAPI is configured"""
    try:
        from price_tracker.api_config import API_CONFIG, is_api_enabled
        
        print("\n🔍 Checking SerpAPI Configuration")
        print("=" * 60)
        
        serpapi_config = API_CONFIG.get('serpapi', {})
        api_key = serpapi_config.get('key', '')
        is_enabled = serpapi_config.get('enabled', False)
        
        print(f"Enabled: {'✅ Yes' if is_enabled else '❌ No'}")
        print(f"API Key: {'✅ Configured' if api_key and api_key != 'YOUR_SERPAPI_KEY_HERE' else '❌ Not configured'}")
        print(f"Rate Limit: {serpapi_config.get('rate_limit', 'Unknown')} searches/month")
        
        if not is_enabled:
            print("\n⚠️ SerpAPI is not enabled!")
            print("   Enable it in price_tracker/api_config.py")
        
        if not api_key or api_key == 'YOUR_SERPAPI_KEY_HERE':
            print("\n⚠️ SerpAPI key is not configured!")
            print("   Add your API key to price_tracker/api_config.py")
            print("   OR set SERPAPI_KEY environment variable")
        
        if is_enabled and api_key and api_key != 'YOUR_SERPAPI_KEY_HERE':
            print("\n✅ SerpAPI is ready to use!")
            return True
        
        print("=" * 60)
        return False
        
    except Exception as e:
        print(f"❌ Error checking configuration: {e}")
        return False

if __name__ == "__main__":
    print("🛍️ Smart Shopper - SerpAPI Integration Test")
    print("=" * 60)
    
    # Check configuration first
    if check_serpapi_config():
        print("\n")
        test_serpapi()
    else:
        print("\n❌ Please configure SerpAPI before running tests")
        print("   See instructions above")
