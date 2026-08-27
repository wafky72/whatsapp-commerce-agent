from typing import List, Dict, Any, Optional

class CartManager:
    """
    Manages simple in-memory shopping carts for sessions.
    In production, this would use Redis or a database.
    """
    def __init__(self):
        # Maps session_id (wa_id) -> List of items
        self.carts: Dict[str, List[Dict[str, Any]]] = {}

    def get_cart(self, session_id: str) -> List[Dict[str, Any]]:
        return self.carts.get(session_id, [])

    def add_item(self, session_id: str, product: Dict[str, Any], quantity: int = 1) -> Dict[str, Any]:
        """
        Add item to cart. Returns the updated cart summary.
        """
        if session_id not in self.carts:
            self.carts[session_id] = []
        
        # Check if item exists
        for item in self.carts[session_id]:
            if item['id'] == product['id']:
                item['quantity'] += quantity
                return self.get_cart_summary(session_id)
        
        # Add new
        self.carts[session_id].append({
            "id": product['id'],
            "name": product['name'],
            "price": product['price'],
            "currency": product.get("currency", "USD"),
            "quantity": quantity,
            "image": product.get("images", [{}])[0].get("src", "")
        })
        
        return self.get_cart_summary(session_id)

    def get_cart_summary(self, session_id: str) -> Dict[str, Any]:
        cart = self.get_cart(session_id)
        total = sum(float(item['price']) * item['quantity'] for item in cart)
        return {
            "items": cart,
            "count": sum(item['quantity'] for item in cart),
            "total": round(total, 2),
            "currency": cart[0]['currency'] if cart else "USD"
        }

    def clear_cart(self, session_id: str):
        if session_id in self.carts:
            del self.carts[session_id]
