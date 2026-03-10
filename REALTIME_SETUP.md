# 🚀 Real-Time Price Monitoring Setup Guide

## Quick Start

### 1. Verify SerpAPI Configuration

Your SerpAPI key is already configured in `price_tracker/api_config.py`:
```python
'serpapi': {
    'key': '0b8a689e20eb31fdd7523c36f7026b45a9aeae87934ca0c8f06799d57abfa4c9',
    'enabled': True
}
```

✅ **Status**: Ready to use!

### 2. Test SerpAPI Connection

```bash
python test_serpapi.py
```

This will test SerpAPI with real Amazon India products.

### 3. Start Real-Time Monitoring

```bash
python realtime_monitor.py
```

Choose your monitoring frequency:
- **Conservative (30 min)**: Best for staying under rate limits
- **Balanced (10 min)**: Good balance of speed and reliability
- **Aggressive (5 min)**: Near real-time updates
- **Ultra-Fast (2 min)**: Maximum speed (watch rate limits!)

## 📋 Products Configuration

Edit `products.json` to add/modify products:

```json
[
  {
    "url": "https://www.amazon.in/dp/B08FC5L3RG",
    "warn_price": 45000,
    "name": "PlayStation 5 Console"
  },
  {
    "url": "https://www.amazon.in/dp/B0D1XD1ZV3",
    "warn_price": 70000,
    "name": "iPhone 15 (128 GB) - Black"
  }
]
```

## 🔑 SerpAPI Features

- ✅ Real Amazon product data
- ✅ Accurate pricing information
- ✅ Product ratings and reviews
- ✅ Availability status
- ✅ 100 searches/month (free tier)

## ⚙️ Monitoring Intervals

| Interval | Checks/Day | Monthly Usage | Recommended For |
|----------|------------|---------------|-----------------|
| 30 min   | 48         | ~1,440        | Multiple products |
| 10 min   | 144        | ~4,320        | Few products |
| 5 min    | 288        | ~8,640        | Single product |
| 2 min    | 720        | ~21,600       | Testing only |

**Note**: With 100 searches/month free tier, 30-minute intervals work best for 2-3 products.

## 📧 Email Alerts

Email is already configured in `config.json`:
- **Sender**: smartshopper202526@gmail.com
- **Receiver**: smartshopper202526@gmail.com

Alerts are sent when:
- Price drops below your threshold
- Product becomes available

## 🛠️ Advanced Usage

### Set Environment Variable (Optional)

For better security, use environment variable:

**Windows CMD:**
```cmd
set SERPAPI_KEY=0b8a689e20eb31fdd7523c36f7026b45a9aeae87934ca0c8f06799d57abfa4c9
```

**Windows PowerShell:**
```powershell
$env:SERPAPI_KEY="0b8a689e20eb31fdd7523c36f7026b45a9aeae87934ca0c8f06799d57abfa4c9"
```

**Permanent (Windows):**
```cmd
setx SERPAPI_KEY "0b8a689e20eb31fdd7523c36f7026b45a9aeae87934ca0c8f06799d57abfa4c9"
```

Then update `price_tracker/api_config.py`:
```python
'serpapi': {
    'key': os.environ.get('SERPAPI_KEY', ''),
    'enabled': True
}
```

### Custom Monitoring Script

```python
from realtime_monitor import RealtimeMonitor

# Create monitor with 15-minute interval
monitor = RealtimeMonitor(check_interval_minutes=15)

# Start monitoring
monitor.start_monitoring()
```

## 🔍 Monitoring Output

```
🔍 Check #1: PlayStation 5 Console
💰 Current Price: ₹49,990.00
🎯 Alert Price: ₹45,000.00
💰 Price above threshold by ₹4,990.00
⏰ Next check in 30 minutes...
```

When price drops:
```
🚨 PRICE DROP DETECTED!
   Savings: ₹5,990.00
✅ Alert sent for PlayStation 5 Console
```

## 📊 Rate Limiting

SerpAPI free tier: **100 searches/month**

To maximize usage:
1. Use 30-minute intervals for multiple products
2. Use 10-minute intervals for 1-2 products
3. Monitor only high-priority products
4. Consider upgrading for more searches

## 🐛 Troubleshooting

### "SerpAPI key not found"
- Check `price_tracker/api_config.py`
- Verify `enabled: True`
- Ensure key is not empty

### "Rate limit exceeded"
- Wait for monthly reset
- Reduce monitoring frequency
- Upgrade SerpAPI plan

### "Could not fetch price"
- Check product URL is valid
- Verify product is available on Amazon India
- Check internet connection

## 🎯 Best Practices

1. **Start with Conservative**: Use 30-minute intervals initially
2. **Monitor Few Products**: Focus on high-priority items
3. **Test First**: Run `test_serpapi.py` before monitoring
4. **Check Logs**: Review alerts in `~/price-tracker/price_alerts.log`
5. **Upgrade if Needed**: Consider paid plan for more products

## 📚 Additional Resources

- **SerpAPI Dashboard**: https://serpapi.com/dashboard
- **API Documentation**: https://serpapi.com/amazon-product-api
- **Usage Stats**: Check your dashboard for remaining searches

---

**Happy Monitoring! 🛍️**
