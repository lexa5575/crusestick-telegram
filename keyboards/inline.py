from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List


def get_main_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="📦 Каталог", callback_data="catalog")],
        [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_catalog_menu(products: List) -> InlineKeyboardMarkup:
    keyboard = []
    
    for product in products:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{product.name} - {product.price} руб.",
                callback_data=f"product_{product.id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_product_menu(product_id: int) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="🛒 Добавить в корзину", callback_data=f"add_to_cart_{product_id}")],
        [InlineKeyboardButton(text="🔙 К каталогу", callback_data="catalog")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_cart_menu(cart_items: List) -> InlineKeyboardMarkup:
    keyboard = []
    
    for item in cart_items:
        keyboard.append([
            InlineKeyboardButton(
                text=f"❌ {item.product.name}",
                callback_data=f"remove_from_cart_{item.product.id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton(text="💳 Оформить заказ", callback_data="checkout")])
    keyboard.append([InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)