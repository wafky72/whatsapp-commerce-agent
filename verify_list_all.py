from woo_handler import WooCommerceHandler

woo = WooCommerceHandler()
print("Testing LIST_ALL functionality (fetching latest products)...")

try:
    products = woo.get_products() # No search term
    if products:
        print(f"Success! Found {len(products)} products.")
        for p in products[:5]:
            print(f"- {p['name']} (Status: {p.get('stock_status')})")
    else:
        print("No products found.")
except Exception as e:
    print(f"Error: {e}")
