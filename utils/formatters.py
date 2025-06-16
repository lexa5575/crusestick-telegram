from datetime import datetime
from typing import List, Dict, Any


def format_order_details(order: Dict[str, Any]) -> str:
    """Форматирует детали заказа для отображения"""
    text = f"🧾 Заказ #{order['id']}\n\n"
    text += f"📅 Дата: {format_date(order['created_at'])}\n"
    text += f"📍 Адрес: {order['address']}\n"
    text += f"📦 Статус: {get_status_emoji(order['status'])} {order['status']}\n\n"
    
    text += "🛒 Товары:\n"
    for item in order.get('items', []):
        text += f"• {item['product_name']} x{item['quantity']} = {format_price(item['price'] * item['quantity'])}\n"
    
    text += f"\n💰 Итого: {format_price(order['total_amount'])}"
    return text


def format_product_card(product: Dict[str, Any]) -> str:
    """Форматирует карточку товара"""
    text = f"📦 {product['name']}\n\n"
    
    if product.get('description'):
        text += f"📝 {product['description']}\n\n"
    
    text += f"💰 Цена: {format_price(product['price'])}"
    return text


def format_cart_summary(cart_items: List[Dict[str, Any]]) -> str:
    """Форматирует содержимое корзины"""
    if not cart_items:
        return "🛒 Ваша корзина пуста"
    
    text = "🛒 Ваша корзина:\n\n"
    total = 0
    
    for item in cart_items:
        item_total = item['product']['price'] * item['quantity']
        text += f"• {item['product']['name']}\n"
        text += f"  {item['quantity']} шт. × {format_price(item['product']['price'])} = {format_price(item_total)}\n\n"
        total += item_total
    
    text += f"💰 Итого: {format_price(total)}"
    return text


def format_price(price_kopecks: int) -> str:
    """Форматирует цену из копеек в рубли"""
    rubles = price_kopecks // 100
    kopecks = price_kopecks % 100
    
    if kopecks == 0:
        return f"{rubles} ₽"
    else:
        return f"{rubles}.{kopecks:02d} ₽"


def format_date(date_str: str) -> str:
    """Форматирует дату для отображения"""
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime("%d.%m.%Y %H:%M")
    except:
        return date_str


def get_status_emoji(status: str) -> str:
    """Возвращает эмодзи для статуса заказа"""
    status_emojis = {
        'pending': '⏳',
        'confirmed': '✅',
        'preparing': '👨‍🍳',
        'delivering': '🚚',
        'delivered': '📦',
        'cancelled': '❌'
    }
    return status_emojis.get(status, '❓')


def format_user_info(user: Dict[str, Any]) -> str:
    """Форматирует информацию о пользователе"""
    text = f"👤 Пользователь: {user.get('first_name', 'Не указано')}"
    
    if user.get('last_name'):
        text += f" {user['last_name']}"
    
    if user.get('username'):
        text += f" (@{user['username']})"
    
    text += f"\n📱 ID: {user['telegram_id']}"
    
    if user.get('phone'):
        text += f"\n📞 Телефон: {user['phone']}"
    
    return text


def pluralize(count: int, forms: List[str]) -> str:
    """Склоняет слово в зависимости от числа"""
    if count % 10 == 1 and count % 100 != 11:
        return forms[0]
    elif 2 <= count % 10 <= 4 and (count % 100 < 10 or count % 100 >= 20):
        return forms[1]
    else:
        return forms[2]


def format_quantity(count: int) -> str:
    """Форматирует количество товаров"""
    forms = ['товар', 'товара', 'товаров']
    return f"{count} {pluralize(count, forms)}"