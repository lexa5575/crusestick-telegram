import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from services.api_client import api_client
from services.cart_service import cart_service
from keyboards.inline import back_to_menu_keyboard, checkout_keyboard
from states.order_states import OrderStates
from utils.formatters import format_cart_message

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data == "my_orders")
async def show_my_orders(callback: CallbackQuery):
    """Show user orders"""
    
    user_id = callback.from_user.id
    
    try:
        # Get user orders
        async with api_client as client:
            orders_response = await client.get_user_orders(user_id)
        
        orders = orders_response.get('orders', [])
        
        if not orders:
            await callback.message.edit_text(
                "📦 <b>Мои заказы</b>\n\n"
                "У вас пока нет заказов.\n"
                "Оформите первый заказ в нашем каталоге!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🛍️ Product Catalog", callback_data="catalog")],
                    [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")]
                ])
            )
            return
        
        # Get last order (first in list)
        last_order = orders[0]
        
        # Format message with order information
        message_text = format_order_details(last_order)
        
        # Create keyboard
        keyboard = []
        
        # If tracking number exists, add tracking button
        if last_order.get('tracking_number'):
            keyboard.append([
                InlineKeyboardButton(
                    text="📦 Track on USPS", 
                    url=f"https://tools.usps.com/go/TrackConfirmAction?tLabels={last_order['tracking_number']}"
                )
            ])
        
        # Reorder button
        keyboard.append([
            InlineKeyboardButton(text="🔄 Reorder", callback_data=f"reorder:{last_order['id']}")
        ])
        
        # Main menu
        keyboard.append([
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        ])
        
        await callback.message.edit_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        
    except Exception as e:
        logger.error(f"Error showing orders for user {user_id}: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при загрузке заказов.\n"
            "Попробуйте позже.",
            reply_markup=back_to_menu_keyboard()
        )

def format_order_details(order: dict) -> str:
    """Format detailed order information"""
    
    # Order statuses with emoji
    status_emoji = {
        'pending': '⏳',
        'paid': '✅', 
        'processing': '🔄',
        'shipped': '📦',
        'delivered': '🎉',
        'cancelled': '❌'
    }
    
    status_text = {
        'pending': 'Ожидает оплаты',
        'paid': 'Оплачен',
        'processing': 'Обрабатывается', 
        'shipped': 'Отправлен',
        'delivered': 'Доставлен',
        'cancelled': 'Отменен'
    }
    
    # Start formatting message
    message = f"📦 <b>Заказ #{order.get('id', 'N/A')}</b>\n\n"
    
    # Order status
    status = order.get('status', 'unknown')
    emoji = status_emoji.get(status, '❓')
    status_name = status_text.get(status, status)
    message += f"{emoji} <b>Статус:</b> {status_name}\n\n"
    
    # Products in order
    products = order.get('products', [])
    if products:
        message += "🛍️ <b>Товары:</b>\n"
        total_items = 0
        for product in products:
            name = product.get('name', 'Неизвестный товар')
            quantity = product.get('quantity', 1)
            price = product.get('price', 0)
            item_total = float(quantity) * float(price)
            
            message += f"• {name}\n"
            message += f"  ${price} × {quantity} = ${item_total:.2f}\n"
            total_items += quantity
        
        message += f"\n📊 <b>Всего товаров:</b> {total_items} шт.\n"
    
    # Total amount
    total_amount = order.get('total_amount', 0)
    message += f"💰 <b>Сумма заказа:</b> ${total_amount}\n\n"
    
    # Shipping address  
    shipping = order.get('shipping_address', {})
    if shipping:
        message += "📍 <b>Адрес доставки:</b>\n"
        
        # Recipient name (Laravel returns 'name' instead of first_name/last_name)
        name = shipping.get('name', '')
        if name:
            message += f"👤 {name}\n"
        
        # Address
        street = shipping.get('street', '')
        house = shipping.get('house', '')  # Laravel использует 'house' вместо 'apartment'
        if street:
            address_line = street
            if house:
                address_line += f", {house}"
            message += f"🏠 {address_line}\n"
        
        # City, state, ZIP (Laravel uses 'postal_code' instead of 'zip_code')
        city = shipping.get('city', '')
        state = shipping.get('state', '')
        postal_code = shipping.get('postal_code', '')
        if city or state or postal_code:
            location = f"{city}, {state} {postal_code}".strip(', ')
            message += f"🌍 {location}\n"
        
        # Phone
        phone = shipping.get('phone', '')
        if phone:
            message += f"📞 {phone}\n"
    
    # Order date (Laravel returns in format 'dates.created_at')
    dates = order.get('dates', {})
    created_at = dates.get('created_at', '') if dates else order.get('created_at', '')
    if created_at:
        message += f"\n📅 <b>Дата заказа:</b> {created_at}"
    
    # Tracking number
    tracking = order.get('tracking_number', '')
    if tracking:
        message += f"\n📮 <b>Трекинг номер:</b> <code>{tracking}</code>"
    
    return message

@router.callback_query(F.data.startswith("reorder:"))
async def handle_reorder(callback: CallbackQuery, state: FSMContext):
    """Handle reorder"""
    
    try:
        order_id = int(callback.data.split(":")[1])
        user_id = callback.from_user.id
        
        # Get user orders для получения данных заказа
        async with api_client as client:
            orders_response = await client.get_user_orders(user_id)
        
        orders = orders_response.get('orders', [])
        target_order = None
        
        # Find target order
        for order in orders:
            if order.get('id') == order_id:
                target_order = order
                break
        
        if not target_order:
            await callback.answer("Order not found", show_alert=True)
            return
        
        # Clear cart
        cart_service.clear_cart(user_id)
        
        # Add products from order to cart
        products = target_order.get('products', [])
        for product in products:
            # Create product object for cart
            cart_product = {
                'id': product['id'],
                'name': product['name'],
                'price': float(product['price']),
                'quantity': product['quantity']
            }
            
            # Add product to cart with needed quantity
            for _ in range(product['quantity']):
                cart_service.add_to_cart(user_id, cart_product)
        
        # Save shipping address in state
        shipping = target_order.get('shipping_address', {})
        
        # Parse name into first_name and last_name
        full_name = shipping.get('name', '').strip()
        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0] if name_parts else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        order_data = {
            'first_name': first_name,
            'last_name': last_name, 
            'street': shipping.get('street', ''),
            'city': shipping.get('city', ''),
            'us_state': shipping.get('state', ''),
            'zip_code': shipping.get('postal_code', ''),
            'phone': shipping.get('phone'),
            'apartment': shipping.get('house'),
            'company': None  # Company is not saved in Laravel
        }
        
        # Save data in state
        await state.update_data(**order_data)
        await state.set_state(OrderStates.selecting_payment)
        
        # Show order confirmation with cart
        cart_items = cart_service.get_cart(user_id)
        cart_total = cart_service.get_cart_total(user_id)
        
        confirmation_text = (
            "🔄 <b>Перезаказ</b>\n\n"
            "Товары добавлены в корзину и адрес заполнен:\n\n"
        )
        
        # Add cart information
        for item in cart_items:
            confirmation_text += f"• {item['name']}\n"
            confirmation_text += f"  ${item['price']} × {item['quantity']} = ${item['total']}\n"
        
        confirmation_text += f"\n💰 <b>Итого: ${cart_total}</b>\n\n"
        
        # Add shipping address
        confirmation_text += "📍 <b>Адрес доставки:</b>\n"
        confirmation_text += f"👤 {first_name} {last_name}\n"
        confirmation_text += f"🏠 {order_data['street']}"
        if order_data.get('apartment'):
            confirmation_text += f", {order_data['apartment']}"
        confirmation_text += f"\n🌍 {order_data['city']}, {order_data['us_state']} {order_data['zip_code']}\n"
        if order_data.get('phone'):
            confirmation_text += f"📞 {order_data['phone']}\n"
        
        confirmation_text += "\nВыберите способ оплаты:"
        
        await callback.message.edit_text(
            confirmation_text,
            reply_markup=checkout_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error processing reorder: {e}")
        await callback.answer("Error processing reorder", show_alert=True)