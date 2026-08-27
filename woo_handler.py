import os
from woocommerce import API
import requests
from dotenv import load_dotenv

load_dotenv()

class WooCommerceHandler:
    def __init__(self):
        self.url = os.getenv("WOO_URL")
        self.consumer_key = os.getenv("WOO_KEY")
        self.consumer_secret = os.getenv("WOO_SECRET")
        
        if self.url and self.consumer_key and self.consumer_secret:
            self.wcapi = API(
                url=self.url,
                consumer_key=self.consumer_key,
                consumer_secret=self.consumer_secret,
                version="wc/v3"
            )
        else:
            self.wcapi = None
            print("Warning: WooCommerce credentials not found. Running in mock mode or limited functionality.")

    def get_products(self, search_term=None):
        """
        Fetch products from WooCommerce.
        If search_term is provided, filters by that term.
        """
        if not self.wcapi:
            return []

        params = {"status": "publish"}
        if search_term:
            params["search"] = search_term

        try:
            response = self.wcapi.get("products", params=params)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error fetching products: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            print(f"Exception fetching products: {e}")
            return []

    def get_product_by_id(self, product_id):
        if not self.wcapi:
            return None
        
        try:
            response = self.wcapi.get(f"products/{product_id}")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error fetching product {product_id}: {e}")
            return None

    def format_product_for_chat(self, product):
        """
        Helper to format a product JSON object into a readable string for the LLM/User.
        Includes detailed info for professional responses.
        """
        import re
        
        def clean_html(raw_html):
            cleanr = re.compile('<.*?>')
            cleantext = re.sub(cleanr, '', raw_html)
            return cleantext.strip()

        name = product.get("name", "Unknown Product")
        price = product.get("price", "N/A")
        # WooCommerce doesn't always send currency_symbol in product objects
        # Set to AED for UAE-based stores
        currency = product.get("currency_symbol", "AED ")
        permalink = product.get("permalink", "")
        stock_status = product.get("stock_status", "unknown")
        
        # Get full description or short description
        full_desc = product.get("description", "")
        short_desc = product.get("short_description", "")
        description = clean_html(full_desc) if full_desc else clean_html(short_desc)
        
        # Categories
        categories = [cat["name"] for cat in product.get("categories", [])]
        categories_str = ", ".join(categories)
        
        # Image
        images = product.get("images", [])
        image_url = images[0]["src"] if images else "No image available"

        return (
            f"Product: {name}\n"
            f"Price: {currency}{price}\n"
            f"Stock Status: {stock_status}\n"
            f"Categories: {categories_str}\n"
            f"Description: {description[:1000]}...\n" # Limit to 1000 chars to avoid token limits
            f"Image: {image_url}\n"
            f"Link: {permalink}"
        )

    def get_order_by_id(self, order_id):
        """
        Fetch order details by ID.
        """
        if not self.wcapi:
            return None
        
        try:
            response = self.wcapi.get(f"orders/{order_id}")
            if response.status_code == 200:
                order = response.json()
                return {
                    "id": order.get("id"),
                    "status": order.get("status"),
                    "total": order.get("total"),
                    "currency": order.get("currency", "AED"),  # Default to AED
                    "date_created": order.get("date_created"),
                    "line_items": [
                        f"{item['name']} x {item['quantity']}" 
                        for item in order.get("line_items", [])
                    ]
                }
            return None
        except Exception as e:
            print(f"Error fetching order {order_id}: {e}")
            return None
