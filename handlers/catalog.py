from aiogram import Router, F
from aiogram.types import CallbackQuery
from keyboards.inline import categories_keyboard, products_keyboard, product_detail_keyboard, back_to_menu_keyboard
from services.api_client import api_client
from utils.formatters import format_product_message

router = Router()

@router.callback_query(F.data == "catalog")
async def show_catalog(callback: CallbackQuery):
    """Show catalog - categories"""
    
    async with api_client as client:
        categories = await client.get_categories()
    
    if not categories:
        await callback.message.edit_text(
            "😔 No categories available yet",
            reply_markup=back_to_menu_keyboard()
        )
        return
    
    await callback.message.edit_text(
        "📂 <b>Choose a category:</b>",
        reply_markup=categories_keyboard(categories)
    )

@router.callback_query(F.data.startswith("category:"))
async def show_category_products(callback: CallbackQuery):
    """Show category products"""
    
    category_id = int(callback.data.split(":")[1])
    
    async with api_client as client:
        products = await client.get_products(category_id=category_id)
    
    if not products:
        await callback.message.edit_text(
            "😔 No products in this category yet",
            reply_markup=back_to_menu_keyboard()
        )
        return
    
    await callback.message.edit_text(
        f"🛍️ <b>Category products:</b>",
        reply_markup=products_keyboard(products, category_id)
    )

@router.callback_query(F.data.startswith("product:"))
async def show_product_detail(callback: CallbackQuery):
    """Show product details"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Product detail requested: {callback.data}")
    product_id = int(callback.data.split(":")[1])
    logger.info(f"Looking for product ID: {product_id}")
    
    async with api_client as client:
        # First try to get all products
        products = await client.get_products()
        logger.info(f"Total products received from get_products(): {len(products)}")
        product = next((p for p in products if p['id'] == product_id), None)
        
        # If product not found - try searching in categories
        if not product:
            logger.info(f"Product {product_id} not found in main list, searching in categories...")
            categories = await client.get_categories()
            for category in categories:
                category_products = await client.get_products(category_id=category['id'])
                logger.info(f"Category {category['id']} has {len(category_products)} products")
                product = next((p for p in category_products if p['id'] == product_id), None)
                if product:
                    logger.info(f"Found product {product_id} in category {category['id']}")
                    break
    
    if not product:
        logger.warning(f"Product {product_id} not found")
        await callback.answer("Product not found", show_alert=True)
        return
    
    message_text = format_product_message(product)
    
    await callback.message.edit_text(
        message_text,
        reply_markup=product_detail_keyboard(product_id, product.get('category_id'))
    )

@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    """Return to main menu"""
    
    welcome_text = (
        f"🛍️ <b>Main Menu</b>\n\n"
        "Choose an action:"
    )
    
    from keyboards.inline import main_menu_keyboard
    await callback.message.edit_text(
        welcome_text,
        reply_markup=main_menu_keyboard()
    )