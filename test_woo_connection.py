import os
from dotenv import load_dotenv
from woocommerce import API
import json

load_dotenv()

url = os.getenv("WOO_URL")
key = os.getenv("WOO_KEY")
secret = os.getenv("WOO_SECRET")

print(f"URL: {url}")
print(f"Key: {key[:5]}...")
print(f"Secret: {secret[:5]}...")

try:
    wcapi = API(
        url=url,
        consumer_key=key,
        consumer_secret=secret,
        version="wc/v3",
        timeout=10
    )
    
    print("Attempting to fetch products...")
    response = wcapi.get("products", params={"per_page": 3})
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        products = response.json()
        print(f"Found {len(products)} products.")
        for p in products:
            print(f"- {p['name']} ({p['price']})")
    else:
        print("Error response:", response.text)

except Exception as e:
    print(f"Connection failed: {e}")
