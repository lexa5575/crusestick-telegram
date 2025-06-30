from typing import Dict, List, Optional
import json

class CartService:
    """Cart service"""
    
    def __init__(self):
        # В памяти для простоты, в продакшне лучше Redis
        self._carts: Dict[int, List[Dict]] = {}
    
    def get_cart(self, user_id: int) -> List[Dict]:
        """Get user cart"""
        return self._carts.get(user_id, [])
    
    def add_to_cart(self, user_id: int, product: Dict, quantity: int = 1) -> bool:
        """Add product to cart"""
        if user_id not in self._carts:
            self._carts[user_id] = []
        
        cart = self._carts[user_id]
        
        # Проверяем, есть ли товар уже в корзине
        for item in cart:
            if item['id'] == product['id']:
                item['quantity'] += quantity
                item['total'] = item['price'] * item['quantity']
                return True
        
        # Добавляем новый товар
        cart_item = {
            'id': product['id'],
            'name': product['name'],
            'price': float(product['price']),
            'quantity': quantity,
            'total': float(product['price']) * quantity
        }
        
        cart.append(cart_item)
        return True
    
    def update_quantity(self, user_id: int, product_id: int, quantity: int) -> bool:
        """Update product quantity in cart"""
        cart = self.get_cart(user_id)
        
        for item in cart:
            if item['id'] == product_id:
                if quantity <= 0:
                    cart.remove(item)
                else:
                    item['quantity'] = quantity
                    item['total'] = item['price'] * quantity
                return True
        
        return False
    
    def remove_from_cart(self, user_id: int, product_id: int) -> bool:
        """Remove product from cart"""
        return self.update_quantity(user_id, product_id, 0)
    
    def clear_cart(self, user_id: int) -> None:
        """Clear cart"""
        if user_id in self._carts:
            self._carts[user_id] = []
    
    def get_cart_total(self, user_id: int) -> float:
        """Get cart total"""
        cart = self.get_cart(user_id)
        return sum(item['total'] for item in cart)
    
    def get_cart_count(self, user_id: int) -> int:
        """Get cart items count"""
        cart = self.get_cart(user_id)
        return sum(item['quantity'] for item in cart)

# Глобальный экземпляр сервиса корзины
cart_service = CartService()