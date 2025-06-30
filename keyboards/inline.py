from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict

def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Main menu keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍️ Catalog", callback_data="catalog")],
        [InlineKeyboardButton(text="🛒 Cart", callback_data="cart")],
        [InlineKeyboardButton(text="📦 My Orders", callback_data="my_orders")],
        [InlineKeyboardButton(text="ℹ️ Help", callback_data="help")]
    ])

def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Back to main menu button"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Main Menu", callback_data="main_menu")]
    ])

def categories_keyboard(categories: list) -> InlineKeyboardMarkup:
    """Keyboard with categories"""
    keyboard = []
    
    for category in categories:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{category['name']} ({category['products_count']})",
                callback_data=f"category:{category['id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton(text="◀️ Main Menu", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def products_keyboard(products: list, category_id: int = None, page: int = 1) -> InlineKeyboardMarkup:
    """Keyboard with products"""
    keyboard = []
    
    for product in products:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{product['name']} - ${product['price']}",
                callback_data=f"product:{product['id']}"
            )
        ])
    
    # Navigation
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="◀️", callback_data=f"products_page:{page-1}:{category_id}"))
    
    nav_buttons.append(InlineKeyboardButton(text="▶️", callback_data=f"products_page:{page+1}:{category_id}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Back buttons
    if category_id:
        keyboard.append([InlineKeyboardButton(text="◀️ To Categories", callback_data="catalog")])
    
    keyboard.append([InlineKeyboardButton(text="◀️ Main Menu", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def product_detail_keyboard(product_id: int, category_id: int = None) -> InlineKeyboardMarkup:
    """Keyboard for product detail page"""
    keyboard = [
        [InlineKeyboardButton(text="🛒 Add to Cart", callback_data=f"add_to_cart:{product_id}")],
        [InlineKeyboardButton(text="🛒 Go to Cart", callback_data="cart")],
        [
            InlineKeyboardButton(text="◀️ Back to Products", callback_data=f"category:{category_id}" if category_id else "catalog"),
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def cart_keyboard(cart_items: List[Dict], user_id: int) -> InlineKeyboardMarkup:
    """Cart keyboard"""
    keyboard = []
    
    if not cart_items:
        keyboard.append([InlineKeyboardButton(text="🛍️ Go Shopping", callback_data="catalog")])
    else:
        # Items in cart
        for item in cart_items:
            keyboard.append([
                InlineKeyboardButton(
                    text=f"📝 {item['name']} (x{item['quantity']})",
                    callback_data=f"edit_cart_item:{item['id']}"
                )
            ])
        
        # Cart management
        keyboard.append([
            InlineKeyboardButton(text="🛒 Checkout", callback_data="checkout"),
            InlineKeyboardButton(text="🗑️ Clear", callback_data="clear_cart")
        ])
        
        keyboard.append([InlineKeyboardButton(text="🛍️ Continue Shopping", callback_data="catalog")])
    
    keyboard.append([InlineKeyboardButton(text="◀️ Main Menu", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def cart_item_keyboard(product_id: int, current_quantity: int) -> InlineKeyboardMarkup:
    """Keyboard for editing cart item"""
    keyboard = [
        [
            InlineKeyboardButton(text="➖", callback_data=f"cart_quantity:{product_id}:{current_quantity-1}"),
            InlineKeyboardButton(text=f"{current_quantity}", callback_data="current_quantity"),
            InlineKeyboardButton(text="➕", callback_data=f"cart_quantity:{product_id}:{current_quantity+1}")
        ],
        [InlineKeyboardButton(text="🗑️ Remove from Cart", callback_data=f"remove_from_cart:{product_id}")],
        [InlineKeyboardButton(text="◀️ Back to Cart", callback_data="cart")]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def checkout_keyboard() -> InlineKeyboardMarkup:
    """Checkout keyboard"""
    keyboard = [
        [InlineKeyboardButton(text="💵 Zelle", callback_data="payment:zelle")],
        [InlineKeyboardButton(text="◀️ Back to Cart", callback_data="cart")]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def order_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Order confirmation keyboard"""
    keyboard = [
        [InlineKeyboardButton(text="✅ Confirm Order", callback_data="confirm_order")],
        [InlineKeyboardButton(text="📝 Edit Address", callback_data="edit_address")],
        [InlineKeyboardButton(text="💰 Enter Promo Code", callback_data="enter_promocode")],
        [InlineKeyboardButton(text="◀️ Back to Cart", callback_data="cart")]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def help_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for help section"""
    keyboard = [
        [InlineKeyboardButton(text="📝 Contact Administrator", callback_data="contact_admin")],
        [InlineKeyboardButton(text="◀️ Main Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def cancel_support_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for canceling support request"""
    keyboard = [
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_support")],
        [InlineKeyboardButton(text="◀️ Main Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def skip_field_keyboard() -> InlineKeyboardMarkup:
    """Skip button for optional fields"""
    keyboard = [
        [InlineKeyboardButton(text="Skip", callback_data="skip_field")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Backward compatibility
def get_main_menu() -> InlineKeyboardMarkup:
    """Backward compatibility"""
    return main_menu_keyboard()