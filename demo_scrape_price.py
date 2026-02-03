import requests
from bs4 import BeautifulSoup
import re

# URL of a product (Amazon India)
URL = "https://www.amazon.in/BELOXY-Saving-Adults-Numbers-Undiyal/dp/B0GFN1SH4M/ref=zg_bs_c_toys_d_sccl_1/524-3058543-2356667?pd_rd_w=cYDyo&content-id=amzn1.sym.b908f532-cbe7-4274-8b24-b671acc58bd2&pf_rd_p=b908f532-cbe7-4274-8b24-b671acc58bd2&pf_rd_r=3T50KGJ3S3H8T2CS46VN&pd_rd_wg=Gs3Jd&pd_rd_r=983ec095-2699-42cf-870a-6a7e0ae3afe5&pd_rd_i=B0GFN1SH4M&th=1"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive"
}

print("🔍 Attempting to scrape Amazon India product...")
print(f"📱 URL: {URL[:60]}...")

response = requests.get(URL, headers=headers)

print(f"📡 Response Status: {response.status_code}")

if response.status_code != 200:
    print("❌ Failed to fetch page")
    print(f"Status Code: {response.status_code}")
    exit()

soup = BeautifulSoup(response.text, "html.parser")

# Try multiple selectors for price (Amazon India uses different classes)
price_selectors = [
    ".a-price-whole",
    ".a-price .a-offscreen",
    ".a-price-range .a-price .a-offscreen",
    ".a-price.a-text-price.a-size-medium.apexPriceToPay .a-offscreen",
    ".a-price-symbol + .a-price-whole",
    "[data-a-price-amount]"
]

price = None
price_text = "Not found"

for selector in price_selectors:
    price_element = soup.select_one(selector)
    if price_element:
        price_text = price_element.get_text().strip()
        # Extract numeric price
        numbers = re.findall(r'[\d,]+\.?\d*', price_text)
        if numbers:
            price = float(numbers[0].replace(',', ''))
            break

# Try multiple selectors for title
title_selectors = [
    "#productTitle",
    ".product-title",
    "h1.a-size-large",
    "h1",
    ".a-size-large.product-title-word-break"
]

title = None
for selector in title_selectors:
    title_element = soup.select_one(selector)
    if title_element:
        title = title_element.get_text().strip()
        break

# Debug: Show what we found
print("\n🔍 DEBUG INFO:")
print(f"Page title: {soup.title.string if soup.title else 'No title'}")
print(f"Page length: {len(response.text)} characters")

# Check if we're blocked
if "robot" in response.text.lower() or "captcha" in response.text.lower():
    print("🚫 Detected anti-bot protection (CAPTCHA/Robot check)")
elif "sign in" in response.text.lower() and len(response.text) < 50000:
    print("🔐 Redirected to sign-in page")
else:
    print("✅ Page content loaded successfully")

print("\n📊 SCRAPING RESULTS:")
if title:
    print(f"📦 Product: {title[:100]}...")
else:
    print("📦 Product: ❌ Title not found")

if price:
    print(f"💰 Price: ₹{price:,.2f}")
else:
    print(f"💰 Price: ❌ {price_text}")

# Show available price elements for debugging
print("\n🔧 DEBUG - Available price elements:")
price_elements = soup.find_all(class_=re.compile("price"))
for i, elem in enumerate(price_elements[:5]):  # Show first 5
    print(f"   {i+1}. Class: {elem.get('class')} | Text: {elem.get_text().strip()[:50]}")

if not price_elements:
    print("   No price elements found with 'price' in class name")

print("\n💡 TIP: Amazon often blocks scrapers. Consider using the API-based approach in api_monitor.py")
