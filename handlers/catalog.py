from aiogram import Router, types, F
from aiogram.types import CallbackQuery
from keyboards.inline import get_catalog_menu, get_product_menu
from database.models import get_products, get_product

router = Router()


@router.callback_query(F.data == "catalog")
async def show_catalog(callback: CallbackQuery):
    products = await get_products()
    await callback.message.edit_text(
        "📦 Каталог товаров:",
        reply_markup=get_catalog_menu(products)
    )


@router.callback_query(F.data.startswith("product_"))
async def show_product(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    product = await get_product(product_id)
    
    if product:
        text = f"📦 {product.name}\n\n"
        text += f"💰 Цена: {product.price} руб.\n"
        text += f"📝 Описание: {product.description}"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_product_menu(product_id)
        )
    else:
        await callback.answer("Товар не найден")