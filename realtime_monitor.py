#!/usr/bin/env python3
"""
Real-Time Price Monitor with SerpAPI
Monitors products at configurable intervals (1-60 minutes)
"""
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from price_tracker.mailer import Mailer
from price_tracker.api_scraper import APIScraper

class RealtimeMonitor:
    def __init__(self, check_interval_minutes=5):
        """
        Initialize real-time monitor
        
        Args:
            check_interval_minutes: How often to check prices (1-60 minutes)
        """
        self.check_interval = check_interval_minutes * 60  # Convert to seconds
        self.mailer = Mailer()
        self.scraper = APIScraper(self.mailer)
        self.products_file = Path('products.json')
        self.running = False
        self.threads = []
        
        # Validate interval
        if check_interval_minutes < 1 or check_interval_minutes > 60:
            raise ValueError("Check interval must be between 1 and 60 minutes")
        
        if check_interval_minutes < 5:
            print("⚠️ WARNING: Intervals below 5 minutes may trigger rate limiting!")
    
    def load_products(self):
        """Load products from JSON file"""
        try:
            if self.products_file.exists():
                with open(self.products_file, 'r') as f:
                    return json.load(f)
            else:
                print("❌ No products.json file found")
                return []
        except Exception as e:
            print(f"❌ Error loading products: {e}")
            return []
    
    def monitor_product(self, product):
        """Monitor a single product continuously"""
        url = product['url']
        warn_price = float(product['warn_price'])
        product_name = product.get('name', 'Unknown Product')
        
        print(f"🎯 Starting real-time monitor for: {product_name}")
        print(f"   Alert Price: ₹{warn_price:,.2f}")
        print(f"   Check Interval: {self.check_interval // 60} minutes")
        
        check_count = 0
        
        while self.running:
            try:
                check_count += 1
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n[{timestamp}] 🔍 Check #{check_count}: {product_name}")
                
                # Use SerpAPI scraper
                result = self.scraper.get_product_data(url)
                
                if result:
                    current_price = result['price']
                    print(f"💰 Current Price: ₹{current_price:,.2f}")
                    print(f"🎯 Alert Price: ₹{warn_price:,.2f}")
                    
                    if current_price < warn_price:
                        savings = warn_price - current_price
                        print(f"🚨 PRICE DROP DETECTED!")
                        print(f"   Savings: ₹{savings:,.2f}")
                        
                        # Send alert
                        self.mailer.send_mail(url, product_name, current_price)
                        print(f"✅ Alert sent for {product_name}")
                    else:
                        difference = current_price - warn_price
                        print(f"💰 Price above threshold by ₹{difference:,.2f}")
                else:
                    print(f"❌ Could not fetch price for {product_name}")
                
                # Wait before next check
                print(f"⏰ Next check in {self.check_interval // 60} minutes...")
                time.sleep(self.check_interval)
                
            except Exception as e:
                print(f"❌ Error monitoring {product_name}: {e}")
                time.sleep(60)  # Wait 1 minute before retry
    
    def start_monitoring(self):
        """Start real-time monitoring for all products"""
        products = self.load_products()
        
        if not products:
            print("❌ No products to monitor")
            print("💡 Add products to products.json first")
            return
        
        print("=" * 70)
        print("🚀 REAL-TIME PRICE MONITOR WITH SERPAPI")
        print("=" * 70)
        print(f"📦 Products to monitor: {len(products)}")
        print(f"⏰ Check interval: {self.check_interval // 60} minutes")
        print(f"🔑 Using SerpAPI for real Amazon data")
        print("=" * 70)
        
        # Test email connection
        self.mailer.log_in()
        if not self.mailer.email_works:
            print("⚠️ Email not configured - alerts will be saved to file")
        else:
            print("✅ Email system ready")
        
        # Show API status
        try:
            from price_tracker.api_config import is_api_enabled
            if is_api_enabled('serpapi'):
                print("✅ SerpAPI is enabled and configured")
            else:
                print("⚠️ SerpAPI not configured - using fallback methods")
        except ImportError:
            print("⚠️ API config not found")
        
        print("=" * 70)
        
        self.running = True
        
        # Start a thread for each product
        for i, product in enumerate(products, 1):
            print(f"\n🔄 Starting monitor {i}/{len(products)}: {product.get('name', 'Unknown')}")
            
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
            print("\n" + "=" * 70)
            print("🎯 REAL-TIME MONITORING ACTIVE!")
            print("=" * 70)
            print("Press Ctrl+C to stop monitoring")
            print("=" * 70 + "\n")
            
            # Keep main thread alive
            while self.running:
                time.sleep(10)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping monitoring...")
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """Stop all monitoring threads"""
        self.running = False
        print("✅ Monitoring stopped")
        print("👋 Goodbye!")


def main():
    """Main function"""
    print("🛍️ Smart Shopper - Real-Time Price Monitor")
    print("=" * 70)
    print("Select monitoring frequency:")
    print("1. 🐌 Conservative (30 minutes) - Recommended")
    print("2. ⚖️  Balanced (10 minutes)")
    print("3. 🚀 Aggressive (5 minutes)")
    print("4. ⚡ Ultra-Fast (2 minutes) - May trigger rate limits!")
    print("5. 🔧 Custom interval")
    print("6. ❌ Exit")
    print("=" * 70)
    
    choice = input("\nSelect option (1-6): ").strip()
    
    intervals = {
        '1': 30,
        '2': 10,
        '3': 5,
        '4': 2
    }
    
    if choice in intervals:
        interval = intervals[choice]
        print(f"\n✅ Starting monitor with {interval}-minute interval...")
        monitor = RealtimeMonitor(check_interval_minutes=interval)
        monitor.start_monitoring()
    elif choice == '5':
        try:
            custom = int(input("Enter interval in minutes (1-60): "))
            if 1 <= custom <= 60:
                print(f"\n✅ Starting monitor with {custom}-minute interval...")
                monitor = RealtimeMonitor(check_interval_minutes=custom)
                monitor.start_monitoring()
            else:
                print("❌ Invalid interval. Must be between 1 and 60 minutes.")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")
    elif choice == '6':
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    main()
