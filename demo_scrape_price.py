import requests
from bs4 import BeautifulSoup

# URL of a product (scraping allowed)
URL = "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(URL, headers=headers)

if response.status_code != 200:
    print("Failed to fetch page")
    exit()

soup = BeautifulSoup(response.text, "html.parser")

# Price is inside <p class="price_color">
price = soup.find("p", class_="price_color").text.strip()

# Product title
title = soup.find("h1").text.strip()

print("✅ SCRAPING SUCCESSFUL")
print("Product:", title)
print("Price:", price)
