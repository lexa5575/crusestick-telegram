from aiogram import Router, types, F
from aiogram.types import CallbackQuery
from keyboards.inline import get_cart_menu, get_main_menu
from database.models import add_to_cart, get_user_cart, remove_from_cart

router = Router()


@router.callback_query(F.data.startswith("add_to_cart_"))
async def add_product_to_cart(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[3])
    user_id = callback.from_user.id
    
    await add_to_cart(user_id, product_id, 1)
    await callback.answer("✅ Товар добавлен в корзину!")


@router.callback_query(F.data == "cart")
async def show_cart(callback: CallbackQuery):
    user_id = callback.from_user.id
    cart_items = await get_user_cart(user_id)
    
    if not cart_items:
        await callback.message.edit_text(
            "🛒 Ваша корзина пуста",
            reply_markup=get_main_menu()
        )
        return
    
    text = "🛒 Ваша корзина:\n\n"
    total = 0
    
    for item in cart_items:
        text += f"{item.product.name} x{item.quantity} = {item.product.price * item.quantity} руб.\n"
        total += item.product.price * item.quantity
    
    text += f"\n💰 Итого: {total} руб."
    
    await callback.message.edit_text(
        text,
        reply_markup=get_cart_menu(cart_items)
    )


@router.callback_query(F.data.startswith("remove_from_cart_"))
async def remove_product_from_cart(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[3])
    user_id = callback.from_user.id
    
    await remove_from_cart(user_id, product_id)
    await callback.answer("❌ Товар удален из корзины!")
    await show_cart(callback)