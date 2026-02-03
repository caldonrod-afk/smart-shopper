#!/usr/bin/env python3
"""
Real-Time Price Monitor using API-based scraping
More reliable than direct web scraping
"""
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from price_tracker.mailer import Mailer
from price_tracker.api_scraper import APIScraper

class APIMonitor:
    def __init__(self, check_interval=300):  # 5 minutes default
        self.check_interval = check_interval
        self.mailer = Mailer()
        self.scraper = APIScraper(self.mailer)
        self.products_file = Path.home() / 'price-tracker' / 'products.json'
        self.running = False
        self.threads = []
        
    def load_products(self):
        """Load products from JSON file"""
        try:
            if self.products_file.exists():
                with open(self.products_file, 'r') as f:
                    return json.load(f)
            else:
                print("❌ No products file found. Run setup first.")
                return []
        except Exception as e:
            print(f"❌ Error loading products: {e}")
            return []
    
    def monitor_product(self, product):
        """Monitor a single product in a separate thread"""
        url = product['url']
        warn_price = float(product['warn_price'])
        product_name = product.get('name', 'Unknown Product')
        
        print(f"🎯 Starting API monitor for: {product_name}")
        
        while self.running:
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n[{timestamp}] 🔍 API Check: {product_name}")
                
                # Use API scraper instead of direct scraping
                alert_sent = self.scraper.check_product(url, warn_price)
                
                if alert_sent:
                    print(f"✅ Alert sent for {product_name}")
                else:
                    print(f"💰 {product_name} - Price still above threshold")
                
                # Wait before next check
                time.sleep(self.check_interval)
                
            except Exception as e:
                print(f"❌ Error monitoring {product_name}: {e}")
                time.sleep(60)  # Wait 1 minute before retry
    
    def start_monitoring(self):
        """Start real-time monitoring for all products"""
        products = self.load_products()
        
        if not products:
            print("❌ No products to monitor")
            return
        
        print(f"🚀 Starting API-based monitoring for {len(products)} products")
        print(f"⏰ Check interval: {self.check_interval} seconds")
        print("🔑 Using API-based scraping for better reliability")
        print("=" * 60)
        
        # Test email connection
        self.mailer.log_in()
        if not self.mailer.email_works:
            print("⚠️ Email not configured - alerts will be saved to file")
        
        # Show API status
        try:
            from price_tracker.api_config import print_api_status
            print_api_status()
            print("=" * 60)
        except ImportError:
            print("⚠️ No API keys configured - using fallback scraping")
            print("=" * 60)
        
        self.running = True
        
        # Start a thread for each product
        for product in products:
            thread = threading.Thread(
                target=self.monitor_product, 
                args=(product,),
                daemon=True
            )
            thread.start()
            self.threads.append(thread)
            
            # Small delay between starting threads
            time.sleep(2)
        
        try:
            print("\n🎯 API-based monitoring active!")
            print("Press Ctrl+C to stop monitoring")
            
            # Keep main thread alive
            while self.running:
                time.sleep(10)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping monitoring...")
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """Stop all monitoring threads"""
        self.running = False
        print("✅ Monitoring stopped")
    
    def add_product(self, url, warn_price, name=None):
        """Add a new product to monitor"""
        products = self.load_products()
        
        new_product = {
            'url': url,
            'warn_price': warn_price,
            'name': name or f"Product {len(products) + 1}",
            'added_date': datetime.now().isoformat()
        }
        
        products.append(new_product)
        
        # Save updated products
        self.products_file.parent.mkdir(exist_ok=True)
        with open(self.products_file, 'w') as f:
            json.dump(products, f, indent=2)
        
        print(f"✅ Added product: {new_product['name']}")
        return new_product

def test_api_scraper():
    """Test the API scraper with sample products"""
    print("🧪 Testing API-based Scraper")
    print("=" * 50)
    
    # Initialize components
    mailer = Mailer()
    scraper = APIScraper(mailer)
    
    # Test products
    test_products = [
        {
            'url': 'https://www.amazon.in/dp/B08FC5L3RG',
            'name': 'PlayStation 5 Console',
            'warn_price': 60000.0
        },
        {
            'url': 'https://www.flipkart.com/apple-iphone-15-pro/p/itm123456',
            'name': 'iPhone 15 Pro',
            'warn_price': 90000.0
        }
    ]
    
    for i, product in enumerate(test_products, 1):
        print(f"\n--- Test {i}/{len(test_products)} ---")
        print(f"🎯 Product: {product['name']}")
        print(f"🔗 URL: {product['url']}")
        print(f"💰 Alert Price: ₹{product['warn_price']}")
        
        try:
            result = scraper.check_product(product['url'], product['warn_price'])
            
            if result:
                print("✅ Price drop detected - alert would be sent!")
            else:
                print("💰 Price above threshold or API fetch successful")
                
        except Exception as e:
            print(f"⚠️ API scraping failed: {e}")
    
    print("\n🎉 API scraper test completed!")

def create_sample_products():
    """Create sample products for API monitoring"""
    products_file = Path.home() / 'price-tracker' / 'products.json'
    products_file.parent.mkdir(exist_ok=True)
    
    sample_products = [
        {
            'url': 'https://www.amazon.in/dp/B08FC5L3RG',
            'warn_price': 45000.0,
            'name': 'PlayStation 5 Console',
            'added_date': datetime.now().isoformat()
        },
        {
            'url': 'https://www.flipkart.com/apple-iphone-15-pro-256gb-natural-titanium/p/itm6ac6485bb80d4',
            'warn_price': 80000.0,
            'name': 'iPhone 15 Pro 256GB',
            'added_date': datetime.now().isoformat()
        },
        {
            'url': 'https://www.amazon.in/dp/B08N5WRWNW',
            'warn_price': 25000.0,
            'name': 'MacBook Air M1',
            'added_date': datetime.now().isoformat()
        }
    ]
    
    with open(products_file, 'w') as f:
        json.dump(sample_products, f, indent=2)
    
    print(f"✅ Sample products created at: {products_file}")
    return sample_products

def main():
    """Main function to run API-based monitoring"""
    print("🛍️ Smart Shopper - API-Based Price Monitor")
    print("=" * 50)
    print("1. 🧪 Test API Scraper")
    print("2. 🔄 Start API Monitoring")
    print("3. 📦 Create Sample Products")
    print("4. 🔑 Check API Status")
    print("5. ❌ Exit")
    
    choice = input("\nSelect option (1-5): ").strip()
    
    if choice == '1':
        test_api_scraper()
    elif choice == '2':
        monitor = APIMonitor(check_interval=300)  # Check every 5 minutes
        monitor.start_monitoring()
    elif choice == '3':
        create_sample_products()
        print("✅ Sample products created!")
    elif choice == '4':
        try:
            from price_tracker.api_config import print_api_status
            print_api_status()
        except ImportError:
            print("❌ API config file not found")
    elif choice == '5':
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()