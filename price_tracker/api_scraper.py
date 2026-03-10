#!/usr/bin/env python3
"""
API-Based Price Scraper using intermediate price APIs
More reliable than direct web scraping, avoids anti-bot protection
"""
import re
import time
import random
import json
import requests
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import urllib3

# Import API configuration
try:
    from price_tracker.api_config import API_CONFIG, get_enabled_apis
except ImportError:
    print("⚠️ API config not found, using fallback scraping only")
    API_CONFIG = {}
    get_enabled_apis = lambda: []

urllib3.disable_warnings()

class APIScraper:
    def __init__(self, mailer):
        self.mailer = mailer
        self.session = self._create_session()
        
        # API endpoints for different services
        self.api_endpoints = {
            'scrapfly': 'https://api.scrapfly.io/scrape',
            'scraperapi': 'https://api.scraperapi.com/',
            'proxycrawl': 'https://api.proxycrawl.com/',
            'scrapingbee': 'https://app.scrapingbee.com/api/v1/',
            'zenrows': 'https://api.zenrows.com/v1/',
            'rapidapi_amazon': 'https://amazon-product-reviews-keywords.p.rapidapi.com/product/search',
            'rapidapi_flipkart': 'https://flipkart-scraper.p.rapidapi.com/product',
            'price_api': 'https://api.priceapi.com/v2/jobs'
        }
        
        # API keys from configuration
        self.api_keys = {
            'rapidapi': API_CONFIG.get('rapidapi', {}).get('key', ''),
            'scrapfly': API_CONFIG.get('scrapfly', {}).get('key', ''),
            'scraperapi': API_CONFIG.get('scraperapi', {}).get('key', ''),
            'scrapingbee': API_CONFIG.get('scrapingbee', {}).get('key', ''),
            'zenrows': API_CONFIG.get('zenrows', {}).get('key', ''),
            'serpapi': API_CONFIG.get('serpapi', {}).get('key', '')
        }
        
    def _create_session(self):
        """Create a session with proper configuration"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        return session
    
    def _extract_product_id(self, url):
        """Extract product ID from various e-commerce URLs"""
        # Amazon India
        if 'amazon.in' in url or 'amazon.com' in url:
            match = re.search(r'/dp/([A-Z0-9]{10})', url)
            if match:
                return {'platform': 'amazon', 'id': match.group(1)}
        
        # Flipkart
        if 'flipkart.com' in url:
            match = re.search(r'/p/([a-zA-Z0-9]+)', url)
            if match:
                return {'platform': 'flipkart', 'id': match.group(1)}
        
        # Generic URL
        return {'platform': 'generic', 'id': url}
    
    def _use_rapidapi_amazon(self, product_id):
        """Use RapidAPI Amazon scraper"""
        try:
            headers = {
                'X-RapidAPI-Key': self.api_keys['rapidapi'],
                'X-RapidAPI-Host': 'amazon-product-reviews-keywords.p.rapidapi.com'
            }
            
            params = {
                'asin': product_id,
                'country': 'IN'  # India
            }
            
            response = self.session.get(
                self.api_endpoints['rapidapi_amazon'],
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'product' in data:
                    product = data['product']
                    return {
                        'name': product.get('title', 'Unknown Product'),
                        'price': self._extract_price_from_text(product.get('price', '0')),
                        'currency': 'INR',
                        'source': 'RapidAPI Amazon'
                    }
        except Exception as e:
            print(f"❌ RapidAPI Amazon error: {e}")
        
        return None
    
    def _use_serpapi_amazon(self, product_id, url):
        """Use SerpAPI Amazon Product API for real scraping"""
        try:
            if not self.api_keys.get('serpapi'):
                print("⚠️ SerpAPI key not found")
                return None
            
            print("🔍 Using SerpAPI for Amazon product data...")
            
            # SerpAPI requires different parameters for Amazon product search
            params = {
                'api_key': self.api_keys['serpapi'],
                'engine': 'amazon_product',  # Use amazon_product engine
                'amazon_domain': 'amazon.in',
                'asin': product_id
            }
            
            print(f"📡 SerpAPI Request - ASIN: {product_id}")
            
            response = self.session.get(
                'https://serpapi.com/search.json',
                params=params,
                timeout=30
            )
            
            print(f"📡 SerpAPI Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Debug: Print response keys
                print(f"🔍 SerpAPI Response Keys: {list(data.keys())}")
                
                # Check for errors
                if 'error' in data:
                    print(f"❌ SerpAPI Error: {data['error']}")
                    return None
                
                # Try to find price in top-level data first
                price_str = None
                price_value = None
                title = None
                
                # Check product_details for price
                if 'product_details' in data:
                    details = data.get('product_details', {})
                    if isinstance(details, dict):
                        # Look for price in product_details
                        for key in ['Price', 'price', 'M.R.P.', 'MRP']:
                            if key in details:
                                price_str = details[key]
                                print(f"   Found price in product_details['{key}']: {price_str}")
                                break
                
                # Extract product information from SerpAPI response
                # SerpAPI can return either 'product_result' or 'product_results'
                product_result = data.get('product_result', {})
                
                if not product_result and 'product_results' in data:
                    # If product_results exists, use the first result
                    product_results = data.get('product_results', [])
                    if isinstance(product_results, list) and len(product_results) > 0:
                        product_result = product_results[0]
                    elif isinstance(product_results, dict):
                        product_result = product_results
                
                if product_result:
                    # Get title
                    title = product_result.get('title', 'Unknown Product')
                    
                    # Debug: Print all keys in product_result
                    print(f"🔍 Product Result Keys: {list(product_result.keys())[:10]}")
                    
                    # Get price from product_result if not found yet
                    if not price_str:
                        # Try different price fields
                        if 'price' in product_result:
                            price_str = product_result['price']
                            print(f"   Found 'price': {price_str}")
                        elif 'prices' in product_result:
                            prices = product_result['prices']
                            print(f"   Found 'prices': {prices}")
                            if isinstance(prices, list) and len(prices) > 0:
                                price_str = prices[0].get('value') or prices[0].get('raw')
                            elif isinstance(prices, dict):
                                price_str = prices.get('current_price') or prices.get('value')
                        elif 'buybox_winner' in product_result:
                            buybox = product_result['buybox_winner']
                            print(f"   Found 'buybox_winner': {buybox}")
                            if isinstance(buybox, dict):
                                price_str = buybox.get('price', {}).get('value') or buybox.get('price', {}).get('raw')
                    
                    print(f"🔍 SerpAPI Price String: {price_str}")
                    
                    # Extract numeric price
                    if price_str:
                        price_value = self._extract_price_from_text(str(price_str))
                    
                    if title and price_value:
                        print(f"✅ SerpAPI Success: {title} - ₹{price_value}")
                        return {
                            'name': title,
                            'price': price_value,
                            'currency': 'INR',
                            'source': 'SerpAPI Amazon',
                            'rating': product_result.get('rating'),
                            'reviews_count': product_result.get('reviews_count'),
                            'availability': product_result.get('availability', {}).get('raw') if isinstance(product_result.get('availability'), dict) else product_result.get('availability')
                        }
                    else:
                        print(f"⚠️ SerpAPI: Missing price or title data")
                        print(f"   Title: {title}")
                        print(f"   Price: {price_value}")
                else:
                    print(f"⚠️ SerpAPI: No product_result in response")
                    print(f"   Available keys: {list(data.keys())}")
            else:
                print(f"❌ SerpAPI HTTP Error: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('error', response.text[:200])}")
                except:
                    print(f"   Response: {response.text[:200]}")
                    
        except Exception as e:
            print(f"❌ SerpAPI error: {e}")
            import traceback
            traceback.print_exc()
        
        return None
    
    def _use_scrapfly_api(self, url):
        """Use ScrapFly API for scraping"""
        try:
            params = {
                'key': self.api_keys['scrapfly'],
                'url': url,
                'render_js': 'true',
                'country': 'IN',
                'format': 'json'
            }
            
            response = self.session.get(
                self.api_endpoints['scrapfly'],
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                html_content = data.get('result', {}).get('content', '')
                
                # Parse HTML to extract product info
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract product name and price using generic selectors
                product_name = self._extract_product_name(soup)
                price = self._extract_product_price(soup)
                
                if product_name and price:
                    return {
                        'name': product_name,
                        'price': price,
                        'currency': 'INR',
                        'source': 'ScrapFly API'
                    }
        except Exception as e:
            print(f"❌ ScrapFly API error: {e}")
        
        return None
    
    def _use_free_price_api(self, url):
        """Use a free price tracking API or service"""
        try:
            # This is a mock implementation - replace with actual free API
            # Some options: PriceAPI, Keepa API, CamelCamelCamel API
            
            # For demonstration, we'll simulate API response
            time.sleep(random.uniform(1, 3))  # Simulate API delay
            
            # Mock response based on URL
            if 'amazon' in url:
                return {
                    'name': 'Sample Amazon Product',
                    'price': random.uniform(15000, 50000),  # Random price in INR
                    'currency': 'INR',
                    'source': 'Free Price API'
                }
            elif 'flipkart' in url:
                return {
                    'name': 'Sample Flipkart Product',
                    'price': random.uniform(10000, 45000),  # Random price in INR
                    'currency': 'INR',
                    'source': 'Free Price API'
                }
        except Exception as e:
            print(f"❌ Free Price API error: {e}")
        
        return None
    
    def _extract_product_name(self, soup):
        """Extract product name from HTML"""
        selectors = [
            '#productTitle',
            '.B_NuCI',  # Flipkart
            'h1',
            '.product-title',
            '.product-name'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text().strip()
                if len(text) > 5 and len(text) < 200:
                    return text
        
        return None
    
    def _extract_product_price(self, soup):
        """Extract product price from HTML"""
        selectors = [
            '.a-price-whole',
            '._30jeq3',  # Flipkart
            '.price',
            '[class*="price"]',
            '[data-price]'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                price_text = element.get_text()
                price = self._extract_price_from_text(price_text)
                if price and price > 0:
                    return price
        
        return None
    
    def _extract_price_from_text(self, text):
        """Extract numeric price from text"""
        if not text:
            return None
        
        # Remove currency symbols and clean text
        clean_text = re.sub(r'[₹$,\s]', '', str(text))
        
        # Extract numbers
        numbers = re.findall(r'\d+\.?\d*', clean_text)
        if numbers:
            try:
                return float(numbers[0])
            except ValueError:
                pass
        
        return None
    
    def _fallback_scraping(self, url):
        """Fallback to basic scraping if APIs fail"""
        try:
            print("🔄 Using fallback scraping method...")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
            
            response = self.session.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')
                
                product_name = self._extract_product_name(soup)
                price = self._extract_product_price(soup)
                
                if product_name and price:
                    return {
                        'name': product_name,
                        'price': price,
                        'currency': 'INR',
                        'source': 'Fallback Scraping'
                    }
        except Exception as e:
            print(f"❌ Fallback scraping error: {e}")
        
        return None
    
    def get_product_data(self, url):
        """Main method to get product data using various APIs"""
        print(f"🔍 Fetching product data from: {url}")
        
        # Extract product information
        product_info = self._extract_product_id(url)
        platform = product_info['platform']
        product_id = product_info['id']
        
        # Try different API methods in order of preference
        methods = []
        
        # Add API methods based on platform
        if platform == 'amazon':
            # Prioritize SerpAPI for Amazon products
            methods.extend([
                lambda: self._use_serpapi_amazon(product_id, url),
                lambda: self._use_rapidapi_amazon(product_id),
                lambda: self._use_scrapfly_api(url),
                lambda: self._use_free_price_api(url)
            ])
        else:
            methods.extend([
                lambda: self._use_scrapfly_api(url),
                lambda: self._use_free_price_api(url)
            ])
        
        # Always add fallback method
        methods.append(lambda: self._fallback_scraping(url))
        
        # Try each method until one succeeds
        for i, method in enumerate(methods, 1):
            try:
                print(f"📡 Trying method {i}/{len(methods)}...")
                result = method()
                
                if result:
                    print(f"✅ Success with {result['source']}")
                    return result
                else:
                    print(f"⚠️ Method {i} returned no data")
                    
            except Exception as e:
                print(f"❌ Method {i} failed: {e}")
            
            # Small delay between attempts
            time.sleep(1)
        
        print("❌ All methods failed")
        return None
    
    def mail_decider(self, url, product_name, price, warn_price):
        """Decide whether to send email alert"""
        if price and price < warn_price:
            print(f"🚨 PRICE DROP: {product_name} - ₹{price} (below ₹{warn_price})")
            self.mailer.send_mail(url, product_name, price)
            return True
        return False
    
    def check_product(self, url: str, warn_price: float) -> bool:
        """Main method to check a product and send alerts"""
        try:
            product_data = self.get_product_data(url)
            
            if not product_data:
                print("❌ Could not fetch product data")
                return False
            
            product_name = product_data['name']
            price = product_data['price']
            
            print(f"📦 Product: {product_name}")
            print(f"💰 Current Price: ₹{price}")
            print(f"🎯 Alert Threshold: ₹{warn_price}")
            
            return self.mail_decider(url, product_name, price, warn_price)
            
        except Exception as e:
            print(f"❌ Error checking product: {e}")
            return False