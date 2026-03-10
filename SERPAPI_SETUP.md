# SerpAPI Setup Guide

## 🚀 Quick Setup

SerpAPI has been integrated into your Smart Shopper project for real Amazon product scraping!

### Step 1: Get Your API Key

1. **Sign up** at: https://serpapi.com/
2. **Free tier includes**: 100 searches/month
3. **Get your API key** from the dashboard

### Step 2: Configure API Key

**Option A: Environment Variable (Recommended)**
```bash
# Windows PowerShell
$env:SERPAPI_KEY="your_api_key_here"

# Windows CMD
set SERPAPI_KEY=your_api_key_here

# Linux/Mac
export SERPAPI_KEY="your_api_key_here"
```

**Option B: Edit Configuration File**
1. Open `price_tracker/api_config.py`
2. Find the `serpapi` section
3. Replace `'YOUR_SERPAPI_KEY_HERE'` with your actual API key:
```python
'serpapi': {
    'key': 'your_actual_api_key_here',  # Replace this
    'enabled': True,
    ...
}
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Test SerpAPI

```bash
python test_serpapi.py
```

## 🎯 How It Works

### API Priority Order

When monitoring Amazon products, the system tries APIs in this order:

1. **SerpAPI** (Primary) - Real Amazon data
2. **RapidAPI** (Fallback) - Alternative Amazon API
3. **ScrapFly** (Fallback) - HTML scraping
4. **Direct Scraping** (Last resort) - Basic scraping

### What SerpAPI Provides

- ✅ **Real product data** from Amazon India
- ✅ **Current prices** in Indian Rupees (₹)
- ✅ **Product titles** and descriptions
- ✅ **Ratings** and review counts
- ✅ **Availability** status
- ✅ **No anti-bot issues** - SerpAPI handles it

### Example Response

```python
{
    'name': 'PlayStation 5 Console',
    'price': 47500.0,
    'currency': 'INR',
    'source': 'SerpAPI Amazon',
    'rating': 4.5,
    'reviews_count': 1234,
    'availability': 'In Stock'
}
```

## 📊 Usage in Your Project

### Automatic Integration

SerpAPI is automatically used when:
- Monitoring Amazon India products
- API key is configured
- SerpAPI is enabled in config

### Manual Testing

```python
from price_tracker.mailer import Mailer
from price_tracker.api_scraper import APIScraper

# Initialize
mailer = Mailer()
scraper = APIScraper(mailer)

# Get product data
url = "https://www.amazon.in/dp/B08FC5L3RG"
data = scraper.get_product_data(url)

print(f"Product: {data['name']}")
print(f"Price: ₹{data['price']}")
```

### With Monitoring System

```bash
# Start API monitor
python api_monitor.py

# Select option 2 (Start API Monitoring)
# SerpAPI will be used automatically for Amazon products
```

## 💰 Pricing

### Free Tier
- **100 searches/month**
- Perfect for personal use
- No credit card required

### Paid Plans
- **$50/month**: 5,000 searches
- **$125/month**: 15,000 searches
- **$250/month**: 30,000 searches

### Cost Optimization Tips

1. **Cache results** - Don't check same product too frequently
2. **Set reasonable intervals** - Check every 5-15 minutes, not every second
3. **Monitor selectively** - Only track products you're seriously interested in
4. **Use fallback APIs** - System automatically falls back if SerpAPI quota is exceeded

## 🔧 Configuration Options

### Amazon Domains

```python
'amazon_domain': 'amazon.in',  # India (default)
# Other options:
# 'amazon.com'  # USA
# 'amazon.co.uk'  # UK
# 'amazon.de'  # Germany
```

### Search Parameters

```python
'params': {
    'engine': 'amazon',
    'amazon_domain': 'amazon.in',
    'gl': 'in',  # Geolocation: India
    'hl': 'en'   # Language: English
}
```

## 🐛 Troubleshooting

### "API key not configured"
- Check environment variable: `echo $env:SERPAPI_KEY`
- Or verify key in `api_config.py`

### "Rate limit exceeded"
- You've used your monthly quota
- Wait for next month or upgrade plan
- System will automatically use fallback APIs

### "No product data returned"
- Check if product URL is valid
- Verify product is available on Amazon India
- Check SerpAPI dashboard for error messages

## 📚 Resources

- **SerpAPI Docs**: https://serpapi.com/amazon-product-api
- **Dashboard**: https://serpapi.com/dashboard
- **Pricing**: https://serpapi.com/pricing
- **Support**: https://serpapi.com/contact

## ✅ Verification

Run this to verify setup:

```bash
python test_serpapi.py
```

Expected output:
```
✅ SerpAPI is ready to use!
🔍 Fetching product data from Amazon...
✅ Successfully fetched product data!
📦 Product Name: PlayStation 5 Console
💰 Current Price: ₹47,500.00
📡 Data Source: SerpAPI Amazon
```

---

**Happy Price Tracking! 🛍️**
