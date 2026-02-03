#!/usr/bin/env python3
"""
Enhanced Real-Time Web Scraper with Anti-Bot Evasion
Supports real-time scraping from major e-commerce websites
"""
import re
import time
import random
import json
from datetime import datetime
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3

urllib3.disable_warnings()

class EnhancedScraper:
    def __init__(self, mailer):
        self.mailer = mailer
        self.session = self._create_session()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        
    def _create_session(self):
        """Create a session with retry strategy and proper headers"""
        session = requests.Session()
        
        # Retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _get_random_headers(self):
        """Generate random headers to avoid detection"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
    
    def _request_with_retry(self, url, max_retries=3):
        """Make request with random delays and headers"""
        for attempt in range(max_retries):
            try:
                # Random delay to avoid rate limiting
                time.sleep(random.uniform(1, 3))
                
                headers = self._get_random_headers()
                
                response = self.session.get(
                    url, 
                    headers=headers, 
                    timeout=15,
                    verify=False,
                    allow_redirects=True
                )
                
                if response.status_code == 200:
                    return BeautifulSoup(response.content, 'html.parser')
                elif response.status_code == 429:  # Rate limited
                    print(f"⏳ Rate limited, waiting {2 ** attempt} seconds...")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    print(f"⚠️ HTTP {response.status_code} for {url}")
                    
            except Exception as e:
                print(f"❌ Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    
        return None
    
    def _extract_price(self, text):
        """Extract price from text using multiple patterns"""
        if not text:
            return None
            
        # Remove common currency symbols and clean text
        clean_text = re.sub(r'[^\d.,\s]', '', text.replace(',', '.'))
        
        # Try different price patterns
        patterns = [
            r'\d+\.\d{2}',  # 123.45
            r'\d+,\d{2}',   # 123,45
            r'\d+\.\d+',    # 123.4
            r'\d+',         # 123
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, clean_text)
            if matches:
                try:
                    return float(matches[0].replace(',', '.'))
                except ValueError:
                    continue
                    
        return None
    
    def mail_decider(self, url, product_name, price, warn_price):
        """Decide whether to send email alert"""
        if price and price < warn_price:
            print(f"🚨 PRICE DROP: {product_name} - ₹{price} (below ₹{warn_price})")
            self.mailer.send_mail(url, product_name, price)
            return True
        return False
    
    # Enhanced Amazon scraper
    def check_amazon_product(self, url: str, warn_price: float) -> bool:
        """Enhanced Amazon product scraper"""
        soup = self._request_with_retry(url)
        if not soup:
            return False
            
        try:
            # Multiple selectors for product name
            product_name = None
            name_selectors = [
                '#productTitle',
                '.product-title',
                'h1.a-size-large',
                '[data-automation-id="product-title"]'
            ]
            
            for selector in name_selectors:
                element = soup.select_one(selector)
                if element:
                    product_name = element.get_text().strip()
                    break
            
            if not product_name:
                print("❌ Could not find product name")
                return False
            
            # Multiple selectors for price
            price = None
            price_selectors = [
                '.a-price-whole',
                '#priceblock_dealprice',
                '#priceblock_ourprice',
                '.a-price .a-offscreen',
                '[data-automation-id="product-price"]',
                '.a-price-range .a-price .a-offscreen'
            ]
            
            for selector in price_selectors:
                element = soup.select_one(selector)
                if element:
                    price_text = element.get_text()
                    price = self._extract_price(price_text)
                    if price:
                        break
            
            if not price:
                print("❌ Could not find price")
                return False
                
            print(f"✅ Amazon: {product_name} - ₹{price}")
            return self.mail_decider(url, product_name, price, warn_price)
            
        except Exception as e:
            print(f"❌ Amazon scraping error: {e}")
            return False
    
    # Enhanced eBay scraper
    def check_ebay_product(self, url: str, warn_price: float) -> bool:
        """Enhanced eBay product scraper"""
        soup = self._request_with_retry(url)
        if not soup:
            return False
            
        try:
            # Product name
            name_selectors = [
                'h1#x-title-label-lbl',
                '.x-item-title-label h1',
                'h1.it-ttl'
            ]
            
            product_name = None
            for selector in name_selectors:
                element = soup.select_one(selector)
                if element:
                    product_name = element.get_text().strip()
                    break
            
            if not product_name:
                print("❌ Could not find eBay product name")
                return False
            
            # Price
            price_selectors = [
                '.notranslate',
                '#prcIsum',
                '.u-flL.condText',
                '.notranslate span'
            ]
            
            price = None
            for selector in price_selectors:
                element = soup.select_one(selector)
                if element:
                    price_text = element.get_text()
                    price = self._extract_price(price_text)
                    if price:
                        break
            
            if not price:
                print("❌ Could not find eBay price")
                return False
                
            print(f"✅ eBay: {product_name} - ₹{price}")
            return self.mail_decider(url, product_name, price, warn_price)
            
        except Exception as e:
            print(f"❌ eBay scraping error: {e}")
            return False
    
    # Enhanced Flipkart scraper
    def check_flipkart_product(self, url: str, warn_price: float) -> bool:
        """Enhanced Flipkart product scraper"""
        soup = self._request_with_retry(url)
        if not soup:
            return False
            
        try:
            # Multiple selectors for product name
            product_name = None
            name_selectors = [
                '.B_NuCI',
                '._35KyD6',
                '.x-item-title-label h1',
                'h1.yhB1nd'
            ]
            
            for selector in name_selectors:
                element = soup.select_one(selector)
                if element:
                    product_name = element.get_text().strip()
                    break
            
            if not product_name:
                print("❌ Could not find Flipkart product name")
                return False
            
            # Multiple selectors for price
            price = None
            price_selectors = [
                '._30jeq3._16Jk6d',
                '._1_WHN1',
                '._3I9_wc._2p6lqe',
                '._25b18c'
            ]
            
            for selector in price_selectors:
                element = soup.select_one(selector)
                if element:
                    price_text = element.get_text()
                    price = self._extract_price(price_text)
                    if price:
                        break
            
            if not price:
                print("❌ Could not find Flipkart price")
                return False
                
            print(f"✅ Flipkart: {product_name} - ₹{price}")
            return self.mail_decider(url, product_name, price, warn_price)
            
        except Exception as e:
            print(f"❌ Flipkart scraping error: {e}")
            return False

    # Enhanced Amazon India scraper
    def check_amazon_in_product(self, url: str, warn_price: float) -> bool:
        """Enhanced Amazon India product scraper"""
        soup = self._request_with_retry(url)
        if not soup:
            return False
            
        try:
            # Multiple selectors for product name
            product_name = None
            name_selectors = [
                '#productTitle',
                '.product-title',
                'h1.a-size-large',
                '[data-automation-id="product-title"]'
            ]
            
            for selector in name_selectors:
                element = soup.select_one(selector)
                if element:
                    product_name = element.get_text().strip()
                    break
            
            if not product_name:
                print("❌ Could not find Amazon India product name")
                return False
            
            # Multiple selectors for price (Amazon India specific)
            price = None
            price_selectors = [
                '.a-price-whole',
                '#priceblock_dealprice',
                '#priceblock_ourprice',
                '.a-price .a-offscreen',
                '[data-automation-id="product-price"]',
                '.a-price-range .a-price .a-offscreen'
            ]
            
            for selector in price_selectors:
                element = soup.select_one(selector)
                if element:
                    price_text = element.get_text()
                    # Remove ₹ symbol and extract price
                    price_text = price_text.replace('₹', '').replace(',', '')
                    price = self._extract_price(price_text)
                    if price:
                        break
            
            if not price:
                print("❌ Could not find Amazon India price")
                return False
                
            print(f"✅ Amazon India: {product_name} - ₹{price}")
            return self.mail_decider(url, product_name, price, warn_price)
            
        except Exception as e:
            print(f"❌ Amazon India scraping error: {e}")
            return False
    def check_generic_product(self, url: str, warn_price: float) -> bool:
        """Generic product scraper for various e-commerce sites"""
        soup = self._request_with_retry(url)
        if not soup:
            return False
            
        try:
            # Generic product name selectors
            name_selectors = [
                'h1',
                '.product-title',
                '.product-name',
                '[class*="title"]',
                '[class*="name"]'
            ]
            
            product_name = None
            for selector in name_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text().strip()
                    if len(text) > 10 and len(text) < 200:  # Reasonable title length
                        product_name = text
                        break
                if product_name:
                    break
            
            if not product_name:
                product_name = soup.find('title').get_text().strip() if soup.find('title') else "Unknown Product"
            
            # Generic price selectors
            price_selectors = [
                '[class*="price"]',
                '[class*="cost"]',
                '[class*="amount"]',
                '[data-price]',
                '.price',
                '.cost'
            ]
            
            price = None
            for selector in price_selectors:
                elements = soup.select(selector)
                for element in elements:
                    price_text = element.get_text()
                    extracted_price = self._extract_price(price_text)
                    if extracted_price and extracted_price > 0:
                        price = extracted_price
                        break
                if price:
                    break
            
            if not price:
                print("❌ Could not find price")
                return False
                
            print(f"✅ Generic: {product_name} - ₹{price}")
            return self.mail_decider(url, product_name, price, warn_price)
            
        except Exception as e:
            print(f"❌ Generic scraping error: {e}")
            return False
    
    def scrape_product(self, url: str, warn_price: float) -> bool:
        """Main scraping method that detects site and uses appropriate scraper"""
        print(f"🔍 Scraping: {url}")
        
        # Detect website and use appropriate scraper
        if 'amazon.in' in url:
            return self.check_amazon_in_product(url, warn_price)
        elif 'amazon.' in url:
            return self.check_amazon_product(url, warn_price)
        elif 'flipkart.com' in url:
            return self.check_flipkart_product(url, warn_price)
        elif 'ebay.' in url:
            return self.check_ebay_product(url, warn_price)
        else:
            return self.check_generic_product(url, warn_price)