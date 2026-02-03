"""
API Configuration for Price Tracker
Store your API keys here and enable the services you want to use
"""

import os
from typing import Dict, List, Optional

# ============================================================================
# API CONFIGURATION
# ============================================================================

API_CONFIG = {
    # ========================================================================
    # RapidAPI Configuration (Recommended for Beginners)
    # ========================================================================
    # Sign up: https://rapidapi.com/
    # Free tier: 100 requests/month per API
    'rapidapi': {
        'key': os.environ.get('RAPIDAPI_KEY', ''),
        'enabled': False,  # Set to True when you have a key
        'endpoints': {
            'amazon': {
                'host': 'amazon23.p.rapidapi.com',
                'url': 'https://amazon23.p.rapidapi.com/product-details',
                'method': 'GET'
            },
            'flipkart': {
                'host': 'flipkart-scraper.p.rapidapi.com', 
                'url': 'https://flipkart-scraper.p.rapidapi.com/product',
                'method': 'GET'
            },
            'real_time_amazon': {
                'host': 'real-time-amazon-data.p.rapidapi.com',
                'url': 'https://real-time-amazon-data.p.rapidapi.com/product-details',
                'method': 'GET'
            }
        },
        'rate_limit': 100,  # requests per month on free tier
        'timeout': 30
    },
    
    # ========================================================================
    # ScraperAPI Configuration (Best Overall)
    # ========================================================================
    # Sign up: https://www.scraperapi.com/
    # Free tier: 5,000 API credits/month
    # Handles proxies, JavaScript rendering, and anti-bot protection
    'scraperapi': {
        'key': os.environ.get('SCRAPERAPI_KEY', ''),
        'enabled': False,
        'url': 'https://api.scraperapi.com/',
        'params': {
            'render': 'true',  # Enable JavaScript rendering
            'country_code': 'in',  # Set to India
            'premium': 'false',  # Use premium proxies (costs more credits)
            'session_number': '1'  # Keep session for multiple requests
        },
        'rate_limit': 5000,  # API credits per month
        'timeout': 60
    },
    
    # ========================================================================
    # SerpAPI Configuration (Google Shopping)
    # ========================================================================
    # Sign up: https://serpapi.com/
    # Free tier: 100 searches/month
    # Great for getting price from Google Shopping
    'serpapi': {
        'key': os.environ.get('SERPAPI_KEY', ''),
        'enabled': False,
        'url': 'https://serpapi.com/search',
        'params': {
            'engine': 'google_shopping',
            'gl': 'in',  # Country: India
            'hl': 'en'   # Language: English
        },
        'rate_limit': 100,
        'timeout': 30
    },
    
    # ========================================================================
    # Bright Data (formerly Luminati) - Enterprise Solution
    # ========================================================================
    # Sign up: https://brightdata.com/
    # Free trial available, then paid plans
    # Most reliable for large-scale operations
    'brightdata': {
        'username': os.environ.get('BRIGHTDATA_USERNAME', ''),
        'password': os.environ.get('BRIGHTDATA_PASSWORD', ''),
        'enabled': False,
        'zone': 'datacenter',  # 'datacenter', 'residential', or 'mobile'
        'country': 'in',
        'proxy_host': 'brd.superproxy.io',
        'proxy_port': 22225,
        'timeout': 60
    },
    
    # ========================================================================
    # Oxylabs Configuration
    # ========================================================================
    # Sign up: https://oxylabs.io/
    # Professional web scraping infrastructure
    'oxylabs': {
        'username': os.environ.get('OXYLABS_USERNAME', ''),
        'password': os.environ.get('OXYLABS_PASSWORD', ''),
        'enabled': False,
        'url': 'https://realtime.oxylabs.io/v1/queries',
        'source': 'amazon',  # amazon, amazon_search, google_shopping
        'geo_location': 'India',
        'timeout': 60
    },
    
    # ========================================================================
    # ScrapingBee Configuration
    # ========================================================================
    # Sign up: https://www.scrapingbee.com/
    # Free tier: 1,000 API credits
    'scrapingbee': {
        'key': os.environ.get('SCRAPINGBEE_KEY', ''),
        'enabled': False,
        'url': 'https://app.scrapingbee.com/api/v1/',
        'params': {
            'render_js': 'True',
            'premium_proxy': 'False',
            'country_code': 'in'
        },
        'rate_limit': 1000,
        'timeout': 45
    },
    
    # ========================================================================
    # ZenRows Configuration
    # ========================================================================
    # Sign up: https://www.zenrows.com/
    # Free tier: 1,000 requests/month
    'zenrows': {
        'key': os.environ.get('ZENROWS_KEY', ''),
        'enabled': False,
        'url': 'https://api.zenrows.com/v1/',
        'params': {
            'js_render': 'true',
            'antibot': 'true',
            'premium_proxy': 'false'
        },
        'rate_limit': 1000,
        'timeout': 45
    },
    
    # ========================================================================
    # Apify Configuration (Actor-based scraping)
    # ========================================================================
    # Sign up: https://apify.com/
    # Free tier: $5 platform usage per month
    'apify': {
        'token': os.environ.get('APIFY_TOKEN', ''),
        'enabled': False,
        'actors': {
            'amazon': 'junglee/amazon-crawler',
            'flipkart': 'dtrungtin/flipkart-scraper'
        },
        'timeout': 300  # Actors can take longer
    }
}

# ============================================================================
# API HELPER FUNCTIONS
# ============================================================================

def get_enabled_apis() -> List[str]:
    """
    Return list of enabled API services
    
    Returns:
        List of API service names that are enabled
    """
    enabled = []
    for name, config in API_CONFIG.items():
        if config.get('enabled', False):
            # Verify key exists for services that need it
            if 'key' in config and config['key']:
                enabled.append(name)
            elif 'token' in config and config['token']:
                enabled.append(name)
            elif 'username' in config and 'password' in config:
                if config['username'] and config['password']:
                    enabled.append(name)
    
    return enabled


def get_api_key(service: str) -> Optional[str]:
    """
    Get API key for specific service
    
    Args:
        service: Name of the API service
        
    Returns:
        API key string or None if not found
    """
    if service not in API_CONFIG:
        return None
    
    config = API_CONFIG[service]
    
    # Different services use different auth methods
    if 'key' in config:
        return config['key']
    elif 'token' in config:
        return config['token']
    elif 'username' in config:
        return config['username']
    
    return None


def get_api_config(service: str) -> Optional[Dict]:
    """
    Get full configuration for a service
    
    Args:
        service: Name of the API service
        
    Returns:
        Configuration dictionary or None
    """
    return API_CONFIG.get(service, None)


def is_api_enabled(service: str) -> bool:
    """
    Check if an API service is enabled and configured
    
    Args:
        service: Name of the API service
        
    Returns:
        True if enabled and has valid credentials
    """
    if service not in API_CONFIG:
        return False
    
    config = API_CONFIG[service]
    
    if not config.get('enabled', False):
        return False
    
    # Check for credentials
    if 'key' in config:
        return bool(config['key'])
    elif 'token' in config:
        return bool(config['token'])
    elif 'username' in config and 'password' in config:
        return bool(config['username'] and config['password'])
    
    return False


def get_recommended_api() -> Optional[str]:
    """
    Get the recommended API to use based on what's enabled
    
    Returns:
        Name of recommended API or None
    """
    enabled = get_enabled_apis()
    
    if not enabled:
        return None
    
    # Priority order: ScraperAPI > RapidAPI > SerpAPI > Others
    priority = ['scraperapi', 'rapidapi', 'serpapi', 'scrapingbee', 
                'zenrows', 'brightdata', 'oxylabs', 'apify']
    
    for api in priority:
        if api in enabled:
            return api
    
    # Return first enabled if none in priority
    return enabled[0]


def validate_api_config() -> Dict[str, bool]:
    """
    Validate all API configurations
    
    Returns:
        Dictionary with service names and validation status
    """
    validation = {}
    
    for service, config in API_CONFIG.items():
        if not config.get('enabled', False):
            validation[service] = False
            continue
        
        # Check for required credentials
        has_auth = False
        
        if 'key' in config and config['key']:
            has_auth = True
        elif 'token' in config and config['token']:
            has_auth = True
        elif 'username' in config and 'password' in config:
            if config['username'] and config['password']:
                has_auth = True
        
        validation[service] = has_auth
    
    return validation


def print_api_status():
    """Print status of all configured APIs"""
    print("" + "="*70)
    print("API Configuration Status")
    print("="*70)
    
    enabled = get_enabled_apis()
    
    if not enabled:
        print("❌ No APIs are currently enabled")
        print("💡 Enable at least one API in api_config.py to use the price tracker")
        return
    
    print(f"✅ {len(enabled)} API(s) enabled:")
    
    for service in enabled:
        config = API_CONFIG[service]
        rate_limit = config.get('rate_limit', 'Unlimited')
        print(f"  • {service.capitalize()}: {rate_limit} requests/month")
    
    recommended = get_recommended_api()
    if recommended:
        print(f"🎯 Recommended: {recommended.capitalize()}")
    
    validation = validate_api_config()
    invalid = [s for s, v in validation.items() if not v and API_CONFIG[s].get('enabled')]
    
    if invalid:
        print(f"️  Warning: {len(invalid)} enabled API(s) missing credentials:")
        for service in invalid:
            print(f"  • {service.capitalize()}")
    
    print("="*70 + "")


# ============================================================================
# WEBSITE-SPECIFIC CONFIGURATIONS
# ============================================================================

WEBSITE_PATTERNS = {
    'amazon': {
        'domains': ['amazon.in', 'amazon.com', 'amazon.co.uk'],
        'supported_apis': ['rapidapi', 'scraperapi', 'serpapi', 'oxylabs', 'apify'],
        'product_id_regex': r'/dp/([A-Z0-9]{10})',
        'fallback_scraping': True
    },
    'flipkart': {
        'domains': ['flipkart.com'],
        'supported_apis': ['rapidapi', 'scraperapi', 'apify'],
        'product_id_regex': r'/p/[^?]+\?pid=([A-Z0-9]+)',
        'fallback_scraping': True
    },
    'ebay': {
        'domains': ['ebay.com', 'ebay.in', 'ebay.co.uk'],
        'supported_apis': ['scraperapi', 'scrapingbee'],
        'product_id_regex': r'/itm/(\d+)',
        'fallback_scraping': True
    },
    'walmart': {
        'domains': ['walmart.com'],
        'supported_apis': ['scraperapi', 'brightdata', 'oxylabs'],
        'product_id_regex': r'/ip/[^/]+/(\d+)',
        'fallback_scraping': False
    },
    'etsy': {
        'domains': ['etsy.com'],
        'supported_apis': ['scraperapi'],
        'product_id_regex': r'/listing/(\d+)',
        'fallback_scraping': True
    }
}


def get_website_type(url: str) -> Optional[str]:
    """
    Detect website type from URL
    
    Args:
        url: Product URL
        
    Returns:
        Website type (amazon, flipkart, etc.) or None
    """
    url_lower = url.lower()
    
    for site_type, config in WEBSITE_PATTERNS.items():
        for domain in config['domains']:
            if domain in url_lower:
                return site_type
    
    return None


def get_supported_apis_for_url(url: str) -> List[str]:
    """
    Get list of APIs that support scraping this URL
    
    Args:
        url: Product URL
        
    Returns:
        List of supported API names
    """
    site_type = get_website_type(url)
    
    if not site_type:
        return []
    
    supported = WEBSITE_PATTERNS[site_type].get('supported_apis', [])
    enabled = get_enabled_apis()
    
    # Return intersection of supported and enabled
    return [api for api in supported if api in enabled]


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == '__main__':
    # Print status when run directly
    print_api_status()
    
    # Show some examples
    print("Example Usage:")
    print("-" * 70)
    print("from api_config import get_enabled_apis, is_api_enabled")
    print("# Check which APIs are enabled")
    print("enabled = get_enabled_apis()")
    print(f"# Result: {get_enabled_apis()}")
    print("# Check if specific API is enabled")
    print("if is_api_enabled('scraperapi'):")
    print("    print('ScraperAPI is ready to use!')")
    print("-" * 70)
