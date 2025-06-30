from typing import Dict, List, Any
from datetime import datetime

def format_product_message(product: Dict) -> str:
    """Product message formatting"""
    
    message = f"🛍️ <b>{product['name']}</b>\n\n"
    
    message += f"💰 <b>Price: ${product['price']}</b>\n"
    
    if product.get('category'):
        message += f"📂 Category: {product['category']['name']}\n"
    
    # Show product description if available
    if product.get('bot_description'):
        message += f"\n📝 {product['bot_description']}"
    elif product.get('description'):
        message += f"\n📝 {product['description']}"
    
    return message

def format_order_message(order: Dict) -> str:
    """Order message formatting"""
    
    status_emoji = {
        'pending': '⏳',
        'paid': '✅',
        'processing': '🔄',
        'shipped': '📦',
        'delivered': '🎉',
        'cancelled': '❌'
    }
    
    status_text = {
        'pending': 'Pending Payment',
        'paid': 'Paid',
        'processing': 'Processing',
        'shipped': 'Shipped',
        'delivered': 'Delivered',
        'cancelled': 'Cancelled'
    }
    
    message = f"📦 <b>Order #{order['id']}</b>\n\n"
    message += f"{status_emoji.get(order['status'], '❓')} <b>Status:</b> {status_text.get(order['status'], order['status'])}\n\n"
    
    message += "🛍️ <b>Products:</b>\n"
    for item in order['products']:
        message += f"• {item['name']} x{item['quantity']} = ${item['total']}\n"
    
    message += f"\n💰 <b>Total: ${order['total_amount']}</b>\n"
    
    if order.get('promocode'):
        message += f"🎫 Promo code: {order['promocode']} (-${order['discount_amount']})\n"
    
    if order.get('tracking_number'):
        message += f"📍 Tracking: <code>{order['tracking_number']}</code>\n"
    
    message += f"📅 Date: {order['created_at'][:10]}"
    
    return message

def format_cart_message(cart_items: List[Dict], total: float) -> str:
    """Cart message formatting"""
    
    if not cart_items:
        return "🛒 <b>Your cart is empty</b>\n\nAdd products from catalog!"
    
    message = "🛒 <b>Your cart:</b>\n\n"
    
    for item in cart_items:
        message += f"• {item['name']}\n"
        message += f"  Price: ${item['price']} x {item['quantity']} = ${item['total']}\n\n"
    
    message += f"💰 <b>Total: ${total}</b>"
    
    return message

def format_order_confirmation(cart_items: List[Dict], total: float, order_data: Dict) -> str:
    """Order confirmation formatting"""
    
    message = "🛒 <b>Your order:</b>\n\n"
    
    for item in cart_items:
        message += f"• {item['name']}\n"
        message += f"  ${item['price']} x {item['quantity']} = ${item['total']}\n\n"
    
    message += f"💰 <b>Total: ${total}</b>\n\n"
    
    if order_data.get('promocode'):
        message += f"🎫 <b>Promo code:</b> {order_data['promocode']}\n\n"
    
    message += f"📞 <b>Phone:</b> {order_data.get('phone', 'Not specified')}\n\n"
    
    # Format shipping address from separate fields
    address_line = ""
    
    # Collect full address
    name_parts = []
    if order_data.get('first_name'):
        name_parts.append(order_data['first_name'])
    if order_data.get('last_name'):
        name_parts.append(order_data['last_name'])
    
    address_components = []
    if name_parts:
        address_components.append(' '.join(name_parts))
    
    if order_data.get('street'):
        street = order_data['street']
        if order_data.get('apartment'):
            street += f", {order_data['apartment']}"
        address_components.append(street)
    
    location_parts = []
    if order_data.get('city'):
        location_parts.append(order_data['city'])
    if order_data.get('us_state'):
        location_parts.append(order_data['us_state'])
    if order_data.get('zip_code'):
        location_parts.append(order_data['zip_code'])
    
    if location_parts:
        address_components.append(', '.join(location_parts))
    
    if order_data.get('company'):
        address_components.append(f"({order_data['company']})")
    
    if address_components:
        address_line = '\n'.join(address_components)
    else:
        address_line = "Not specified"
    
    message += f"📍 <b>Shipping address:</b>\n{address_line}"
    
    return message


def format_price(price_kopecks: int) -> str:
    """Format price from kopecks to rubles"""
    rubles = price_kopecks // 100
    kopecks = price_kopecks % 100
    
    if kopecks == 0:
        return f"{rubles} ₽"
    else:
        return f"{rubles}.{kopecks:02d} ₽"


def format_date(date_str: str) -> str:
    """Format date for display"""
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime("%d.%m.%Y %H:%M")
    except:
        return date_str


def get_status_emoji(status: str) -> str:
    """Return emoji for order status"""
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
    """Format user information"""
    text = f"👤 User: {user.get('first_name', 'Not specified')}"
    
    if user.get('last_name'):
        text += f" {user['last_name']}"
    
    if user.get('username'):
        text += f" (@{user['username']})"
    
    text += f"\n📱 ID: {user['telegram_id']}"
    
    if user.get('phone'):
        text += f"\n📞 Phone: {user['phone']}"
    
    return text


def pluralize(count: int, forms: List[str]) -> str:
    """Decline word depending on count"""
    if count % 10 == 1 and count % 100 != 11:
        return forms[0]
    elif 2 <= count % 10 <= 4 and (count % 100 < 10 or count % 100 >= 20):
        return forms[1]
    else:
        return forms[2]


def format_quantity(count: int) -> str:
    """Format product quantity"""
    forms = ['product', 'products', 'products']
    return f"{count} {pluralize(count, forms)}"