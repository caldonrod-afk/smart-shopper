"""
Unified Price Scraper
Intelligently uses APIs when available, falls back to direct scraping
"""

import re
import time
import random
import requests
from typing import Optional, Dict, Tuple
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import urllib3

# Import API configuration
try:
    from price_tracker.api_config import (
        get_enabled_apis, is_api_enabled, get_api_config,
        get_website_type, get_supported_apis_for_url
    )
except ImportError:
    print("Warning: API config not found, using fallback scraping only")
    get_enabled_apis = lambda: []
    is_api_enabled = lambda x: False

urllib3.disable_warnings()


class UnifiedScraper:
    """
    Unified scraper that tries multiple methods:
    1. API scraping (fastest, most reliable)
    2. Enhanced web scraping (with anti-bot evasion)
    3. Simple fallback scraping
    """
    
    def __init__(self, mailer=None, database=None):
        """Initialize unified scraper"""
        self.mailer = mailer
        self.database = database
        self.session = self._create_session()
        
        # User agents for rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
        
        # Track API usage
        self.api_calls = {'successful': 0, 'failed': 0}
        self.scraping_calls = {'successful': 0, 'failed': 0}
    
    def _create_session(self):
        """Create requests session with proper configuration"""
        session = requests.Session()
        session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        return session
    
    def scrape_product(self, url: str, warn_price: float) -> bool:
        """Main method to scrape product using best available method"""
        print("\n" + "="*70)
        print(f"Scraping: {url}")
        print(f"Target price: Rs.{warn_price:.2f}")
        print("="*70)
        
        # Get product data using best method
        result = self.get_product_data(url)
        
        if not result:
            print("ERROR: Failed to get product data")
            return False
        
        product_name = result['name']
        price = result['price']
        source = result['source']
        
        print(f"\nProduct: {product_name}")
        print(f"Current price: Rs.{price:.2f} (via {source})")
        
        # Update database if available
        if self.database:
            product = self.database.get_product_by_url(url)
            if product:
                self.database.update_product_price(
                    product['id'], price, source
                )
        
        # Check if alert should be sent
        if price <= warn_price:
            price_drop = warn_price - price
            savings_percent = (price_drop / warn_price) * 100
            
            print(f"\nPRICE DROP DETECTED!")
            print(f"You save: Rs.{price_drop:.2f} ({savings_percent:.1f}%)")
            
            if self.mailer:
                self.mailer.send_mail(url, product_name, price)
                return True
        else:
            diff = price - warn_price
            print(f"Price is Rs.{diff:.2f} above target")
        
        return False
    
    def get_product_data(self, url: str) -> Optional[Dict]:
        """Get product data using the best available method"""
        # Detect website type
        try:
            website_type = get_website_type(url)
            print(f"Detected website: {website_type or 'unknown'}")
        except:
            website_type = None
        
        # Get supported APIs for this URL
        try:
            supported_apis = get_supported_apis_for_url(url)
            if supported_apis:
                print(f"{len(supported_apis)} API(s) available: {', '.join(supported_apis)}")
        except:
            supported_apis = []
        
        # Try methods in order of preference
        methods = []
        
        # 1. Add API methods
        for api in supported_apis:
            if api == 'rapidapi':
                methods.append(('RapidAPI', lambda: self._scrape_via_rapidapi(url, website_type)))
            elif api == 'scraperapi':
                methods.append(('ScraperAPI', lambda: self._scrape_via_scraperapi(url)))
            elif api == 'serpapi':
                methods.append(('SerpAPI', lambda: self._scrape_via_serpapi(url, website_type)))
        
        # 2. Add enhanced web scraping
        methods.append(('Enhanced Scraping', lambda: self._scrape_enhanced(url, website_type)))
        
        # 3. Add simple fallback
        methods.append(('Fallback Scraping', lambda: self._scrape_fallback(url, website_type)))
        
        # Try each method
        for i, (method_name, method_func) in enumerate(methods, 1):
            print(f"\nAttempt {i}/{len(methods)}: {method_name}")
            
            try:
                result = method_func()
                
                if result and result.get('price') and result.get('name'):
                    # Validate result
                    if result['price'] > 0 and len(result['name']) > 3:
                        print(f"SUCCESS via {method_name}")
                        return result
                    else:
                        print(f"Invalid data from {method_name}")
                else:
                    print(f"No data from {method_name}")
                    
            except Exception as e:
                print(f"{method_name} failed: {str(e)[:100]}")
            
            # Small delay between attempts
            if i < len(methods):
                time.sleep(random.uniform(1, 2))
        
        print("ERROR: All methods failed")
        return None
    
    def _scrape_via_rapidapi(self, url: str, website_type: str) -> Optional[Dict]:
        """Scrape using RapidAPI"""
        if not is_api_enabled('rapidapi'):
            return None
        
        config = get_api_config('rapidapi')
        
        if website_type == 'amazon':
            return self._rapidapi_amazon(url, config)
        elif website_type == 'flipkart':
            return self._rapidapi_flipkart(url, config)
        
        return None
    
    def _rapidapi_amazon(self, url: str, config: Dict) -> Optional[Dict]:
        """Scrape Amazon via RapidAPI"""
        try:
            # Extract ASIN
            asin_match = re.search(r'/dp/([A-Z0-9]{10})', url)
            if not asin_match:
                return None
            
            asin = asin_match.group(1)
            
            api_url = config['endpoints']['real_time_amazon']['url']
            headers = {
                'X-RapidAPI-Key': config['key'],
                'X-RapidAPI-Host': config['endpoints']['real_time_amazon']['host']
            }
            
            params = {'asin': asin, 'country': 'IN'}
            
            response = self.session.get(
                api_url, headers=headers, params=params,
                timeout=config['timeout']
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data:
                    product = data['data']
                    
                    return {
                        'name': product.get('product_title', 'Unknown'),
                        'price': self._extract_price_value(
                            product.get('product_price', '0')
                        ),
                        'currency': 'INR',
                        'source': 'RapidAPI Amazon'
                    }
            
            self.api_calls['failed'] += 1
            
        except Exception as e:
            print(f"RapidAPI Amazon error: {e}")
            self.api_calls['failed'] += 1
        
        return None
    
    def _rapidapi_flipkart(self, url: str, config: Dict) -> Optional[Dict]:
        """Scrape Flipkart via RapidAPI"""
        try:
            api_url = config['endpoints']['flipkart']['url']
            headers = {
                'X-RapidAPI-Key': config['key'],
                'X-RapidAPI-Host': config['endpoints']['flipkart']['host']
            }
            
            params = {'url': url}
            
            response = self.session.get(
                api_url, headers=headers, params=params,
                timeout=config['timeout']
            )
            
            if response.status_code == 200:
                data = response.json()
                
                return {
                    'name': data.get('name', 'Unknown Product'),
                    'price': self._extract_price_value(data.get('price', '0')),
                    'currency': 'INR',
                    'source': 'RapidAPI Flipkart'
                }
            
            self.api_calls['failed'] += 1
            
        except Exception as e:
            print(f"RapidAPI Flipkart error: {e}")
            self.api_calls['failed'] += 1
        
        return None
    
    def _scrape_via_scraperapi(self, url: str) -> Optional[Dict]:
        """Scrape using ScraperAPI"""
        if not is_api_enabled('scraperapi'):
            return None
        
        try:
            config = get_api_config('scraperapi')
            
            api_url = config['url']
            params = {
                'api_key': config['key'],
                'url': url,
                **config['params']
            }
            
            response = self.session.get(
                api_url, params=params, timeout=config['timeout']
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Use generic extraction
                name = self._extract_product_name(soup)
                price = self._extract_product_price(soup)
                
                if name and price:
                    self.api_calls['successful'] += 1
                    return {
                        'name': name,
                        'price': price,
                        'currency': 'INR',
                        'source': 'ScraperAPI'
                    }
            
            self.api_calls['failed'] += 1
            
        except Exception as e:
            print(f"ScraperAPI error: {e}")
            self.api_calls['failed'] += 1
        
        return None
    
    def _scrape_via_serpapi(self, url: str, website_type: str) -> Optional[Dict]:
        """Scrape using SerpAPI (Google Shopping)"""
        if not is_api_enabled('serpapi'):
            return None
        
        try:
            config = get_api_config('serpapi')
            
            # Extract product name for search
            product_keywords = self._extract_keywords_from_url(url)
            
            params = {
                'api_key': config['key'],
                'q': product_keywords,
                **config['params']
            }
            
            response = self.session.get(
                config['url'], params=params, timeout=config['timeout']
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'shopping_results' in data and data['shopping_results']:
                    # Get first result
                    result = data['shopping_results'][0]
                    
                    self.api_calls['successful'] += 1
                    return {
                        'name': result.get('title', 'Unknown Product'),
                        'price': self._extract_price_value(
                            result.get('price', '0')
                        ),
                        'currency': 'INR',
                        'source': 'SerpAPI'
                    }
            
            self.api_calls['failed'] += 1
            
        except Exception as e:
            print(f"SerpAPI error: {e}")
            self.api_calls['failed'] += 1
        
        return None
    
    def _scrape_enhanced(self, url: str, website_type: str) -> Optional[Dict]:
        """Enhanced web scraping with anti-bot evasion"""
        try:
            # Random delay
            time.sleep(random.uniform(1, 3))
            
            # Random user agent
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.google.com/',
                'DNT': '1'
            }
            
            response = self.session.get(
                url, headers=headers, timeout=15, verify=False
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Use website-specific extraction
                if website_type:
                    name, price = self._extract_by_website_type(
                        soup, website_type
                    )
                else:
                    name = self._extract_product_name(soup)
                    price = self._extract_product_price(soup)
                
                if name and price:
                    self.scraping_calls['successful'] += 1
                    return {
                        'name': name,
                        'price': price,
                        'currency': 'INR',
                        'source': 'Enhanced Scraping'
                    }
            
            self.scraping_calls['failed'] += 1
            
        except Exception as e:
            print(f"Enhanced scraping error: {e}")
            self.scraping_calls['failed'] += 1
        
        return None
    
    def _scrape_fallback(self, url: str, website_type: str) -> Optional[Dict]:
        """Simple fallback scraping"""
        try:
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                name = self._extract_product_name(soup)
                price = self._extract_product_price(soup)
                
                if name and price:
                    self.scraping_calls['successful'] += 1
                    return {
                        'name': name,
                        'price': price,
                        'currency': 'INR',
                        'source': 'Fallback Scraping'
                    }
            
            self.scraping_calls['failed'] += 1
            
        except Exception as e:
            print(f"Fallback scraping error: {e}")
            self.scraping_calls['failed'] += 1
        
        return None
    
    def _extract_by_website_type(self, soup: BeautifulSoup, 
                                  website_type: str) -> Tuple[Optional[str], Optional[float]]:
        """Extract product data using website-specific selectors"""
        
        if website_type == 'amazon':
            return self._extract_amazon(soup)
        elif website_type == 'flipkart':
            return self._extract_flipkart(soup)
        elif website_type == 'ebay':
            return self._extract_ebay(soup)
        else:
            return self._extract_generic(soup)
    
    def _extract_amazon(self, soup: BeautifulSoup) -> Tuple[Optional[str], Optional[float]]:
        """Extract Amazon product data"""
        # Product name
        name_selectors = ['#productTitle', '.product-title-word-break']
        name = None
        
        for selector in name_selectors:
            element = soup.select_one(selector)
            if element:
                name = element.get_text().strip()
                break
        
        # Price
        price_selectors = [
            '.a-price-whole',
            '#priceblock_dealprice',
            '#priceblock_ourprice',
            '.a-price .a-offscreen'
        ]
        
        price = None
        for selector in price_selectors:
            element = soup.select_one(selector)
            if element:
                price = self._extract_price_value(element.get_text())
                if price:
                    break
        
        return name, price
    
    def _extract_flipkart(self, soup: BeautifulSoup) -> Tuple[Optional[str], Optional[float]]:
        """Extract Flipkart product data"""
        # Product name
        name_selectors = ['.B_NuCI', '._35KyD6', 'h1.yhB1nd']
        name = None
        
        for selector in name_selectors:
            element = soup.select_one(selector)
            if element:
                name = element.get_text().strip()
                break
        
        # Price
        price_selectors = ['._30jeq3', '._1_WHN1', '._3I9_wc']
        price = None
        
        for selector in price_selectors:
            element = soup.select_one(selector)
            if element:
                price = self._extract_price_value(element.get_text())
                if price:
                    break
        
        return name, price
    
    def _extract_ebay(self, soup: BeautifulSoup) -> Tuple[Optional[str], Optional[float]]:
        """Extract eBay product data"""
        # Product name
        name_elem = soup.select_one('h1.x-item-title__mainTitle')
        name = name_elem.get_text().strip() if name_elem else None
        
        # Price
        price_elem = soup.select_one('.x-price-primary')
        price = self._extract_price_value(
            price_elem.get_text()
        ) if price_elem else None
        
        return name, price
    
    def _extract_generic(self, soup: BeautifulSoup) -> Tuple[Optional[str], Optional[float]]:
        """Generic extraction for unknown websites"""
        name = self._extract_product_name(soup)
        price = self._extract_product_price(soup)
        return name, price
    
    def _extract_product_name(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product name using generic selectors"""
        selectors = [
            'h1',
            '.product-title',
            '.product-name',
            '[class*="title"]',
            '[class*="name"]'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().strip()
                # Valid product name: 10-200 characters
                if 10 < len(text) < 200:
                    return text
        
        # Fallback to page title
        title = soup.find('title')
        if title:
            return title.get_text().strip()[:100]
        
        return None
    
    def _extract_product_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract price using generic selectors"""
        selectors = [
            '[class*="price"]',
            '[class*="cost"]',
            '[class*="amount"]',
            '[data-price]',
            '.price',
            '.cost'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                price = self._extract_price_value(element.get_text())
                if price and price > 0:
                    return price
        
        return None
    
    def _extract_price_value(self, text: str) -> Optional[float]:
        """Extract numeric price from text"""
        if not text:
            return None
        
        # Remove currency symbols
        clean = re.sub(r'[₹$€£,\s]', '', str(text))
        
        # Find numbers
        numbers = re.findall(r'\d+\.?\d*', clean)
        
        if numbers:
            try:
                price = float(numbers[0])
                # Sanity check: price should be between 1 and 10 million
                if 1 < price < 10000000:
                    return price
            except ValueError:
                pass
        
        return None
    
    def _extract_keywords_from_url(self, url: str) -> str:
        """Extract search keywords from URL"""
        parsed = urlparse(url)
        path = parsed.path
        
        # Remove common path segments
        keywords = re.sub(r'/(dp|p|product|item|itm)/', ' ', path)
        keywords = re.sub(r'[/_-]', ' ', keywords)
        keywords = re.sub(r'[^a-zA-Z0-9\s]', '', keywords)
        
        return keywords.strip()[:100]
    
    def get_statistics(self) -> Dict:
        """Get scraping statistics"""
        total_api = self.api_calls['successful'] + self.api_calls['failed']
        total_scraping = self.scraping_calls['successful'] + self.scraping_calls['failed']
        
        return {
            'api': {
                'total': total_api,
                'successful': self.api_calls['successful'],
                'failed': self.api_calls['failed'],
                'success_rate': (
                    (self.api_calls['successful'] / total_api * 100)
                    if total_api > 0 else 0
                )
            },
            'scraping': {
                'total': total_scraping,
                'successful': self.scraping_calls['successful'],
                'failed': self.scraping_calls['failed'],
                'success_rate': (
                    (self.scraping_calls['successful'] / total_scraping * 100)
                    if total_scraping > 0 else 0
                )
            }
        }
    
    def print_statistics(self):
        """Print scraping statistics"""
        stats = self.get_statistics()
        
        print("\n" + "="*60)
        print("Scraping Statistics")
        print("="*60)
        
        print("\nAPI Calls:")
        print(f"  Total: {stats['api']['total']}")
        print(f"  Successful: {stats['api']['successful']}")
        print(f"  Failed: {stats['api']['failed']}")
        print(f"  Success Rate: {stats['api']['success_rate']:.1f}%")
        
        print("\nWeb Scraping:")
        print(f"  Total: {stats['scraping']['total']}")
        print(f"  Successful: {stats['scraping']['successful']}")
        print(f"  Failed: {stats['scraping']['failed']}")
        print(f"  Success Rate: {stats['scraping']['success_rate']:.1f}%")
        
        print("="*60 + "\n")


if __name__ == '__main__':
    # Test the scraper
    scraper = UnifiedScraper()
    
    test_url = 'https://www.amazon.in/dp/B09G9HD6PD'
    result = scraper.scrape_product(test_url, warn_price=25000)
    
    # Print statistics
    scraper.print_statistics()
