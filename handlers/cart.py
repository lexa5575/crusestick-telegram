import logging
from typing import Dict
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from config import settings
from keyboards.inline import (
    cart_keyboard, cart_item_keyboard, checkout_keyboard, 
    order_confirmation_keyboard, back_to_menu_keyboard, skip_field_keyboard
)
from services.cart_service import cart_service
from services.api_client import api_client
from states.order_states import OrderStates
from utils.formatters import format_cart_message, format_order_confirmation
from services.admin_notifications import notify_admins_new_order

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data.startswith("add_to_cart:"))
async def add_product_to_cart(callback: CallbackQuery):
    """Add product to cart"""
    
    try:
        logger.info(f"Add to cart callback received: {callback.data}")
        
        product_id = int(callback.data.split(":")[1])
        user_id = callback.from_user.id
        
        logger.info(f"Adding product {product_id} to cart for user {user_id}")
        
        # Get product data from API
        async with api_client as client:
            products = await client.get_products()
            product = next((p for p in products if p['id'] == product_id), None)
        
        if not product:
            logger.warning(f"Product {product_id} not found")
            await callback.answer("Product not found", show_alert=True)
            return
        
        # Add to cart
        cart_service.add_to_cart(user_id, product)
        logger.info(f"Product {product['name']} added to cart for user {user_id}")
        
        # Track cart activity for reminders via Laravel API
        try:
            async with api_client as client:
                await client.track_user_activity(user_id, 'cart_added', {
                    'product_id': product_id, 
                    'product_name': product['name']
                })
        except Exception as e:
            logger.error(f"Failed to track cart activity: {e}")
        
        await callback.answer(f"✅ {product['name']} added to cart")
        
    except Exception as e:
        logger.error(f"Error adding product to cart: {e}")
        await callback.answer("Error adding product to cart", show_alert=True)

@router.callback_query(F.data == "cart")
async def show_cart(callback: CallbackQuery, state: FSMContext):
    """Show cart"""
    
    user_id = callback.from_user.id
    cart_items = cart_service.get_cart(user_id)
    cart_total = cart_service.get_cart_total(user_id)
    
    message_text = format_cart_message(cart_items, cart_total)
    
    if state:
        await state.set_state(OrderStates.viewing_cart)
    
    await callback.message.edit_text(
        message_text,
        reply_markup=cart_keyboard(cart_items, user_id)
    )

@router.callback_query(F.data.startswith("edit_cart_item:"))
async def edit_cart_item(callback: CallbackQuery):
    """Edit cart item"""
    
    product_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    cart_items = cart_service.get_cart(user_id)
    item = next((item for item in cart_items if item['id'] == product_id), None)
    
    if not item:
        await callback.answer("Product not found in cart", show_alert=True)
        return
    
    message_text = (
        f"📝 <b>{item['name']}</b>\n\n"
        f"💰 Price: ${item['price']}\n"
        f"📦 Quantity: {item['quantity']}\n"
        f"💵 Total: ${item['total']}\n\n"
        "Change Quantity:"
    )
    
    await callback.message.edit_text(
        message_text,
        reply_markup=cart_item_keyboard(product_id, item['quantity'])
    )

@router.callback_query(F.data.startswith("cart_quantity:"))
async def update_cart_quantity(callback: CallbackQuery):
    """Update product quantity in cart"""
    
    _, product_id, new_quantity = callback.data.split(":")
    product_id = int(product_id)
    new_quantity = int(new_quantity)
    user_id = callback.from_user.id
    
    if new_quantity <= 0:
        cart_service.remove_from_cart(user_id, product_id)
        await callback.answer("Product deleted from cart")
        await show_cart(callback, None)
        return
    
    cart_service.update_quantity(user_id, product_id, new_quantity)
    
    # Update message
    cart_items = cart_service.get_cart(user_id)
    item = next((item for item in cart_items if item['id'] == product_id), None)
    
    if item:
        message_text = (
            f"📝 <b>{item['name']}</b>\n\n"
            f"💰 Price: ${item['price']}\n"
            f"📦 Quantity: {item['quantity']}\n"
            f"💵 Total: ${item['total']}\n\n"
            "Change Quantity:"
        )
        
        await callback.message.edit_text(
            message_text,
            reply_markup=cart_item_keyboard(product_id, item['quantity'])
        )
    
    await callback.answer(f"Quantity change on {new_quantity}")

@router.callback_query(F.data.startswith("remove_from_cart:"))
async def remove_from_cart(callback: CallbackQuery):
    """Remove product from cart"""
    
    product_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    cart_service.remove_from_cart(user_id, product_id)
    
    await callback.answer("Product deleted from cart")
    await show_cart(callback, None)

@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery):
    """Clear cart"""
    
    user_id = callback.from_user.id
    cart_service.clear_cart(user_id)
    
    await callback.answer("Cart is empty")
    await show_cart(callback, None)

@router.callback_query(F.data == "checkout")
async def start_checkout(callback: CallbackQuery, state: FSMContext):
    """Start checkout process"""
    
    user_id = callback.from_user.id
    cart_items = cart_service.get_cart(user_id)
    
    if not cart_items:
        await callback.answer("Cart is empty", show_alert=True)
        return
    
    # Cancel cart reminders since user is proceeding to checkout
    try:
        async with api_client as client:
            await client.track_user_activity(user_id, 'checkout_started', {})
    except Exception as e:
        logger.error(f"Failed to track checkout activity: {e}")
    
    await state.set_state(OrderStates.entering_first_name)
    
    await callback.message.edit_text(
        "📞 <b>Confirming order</b>\n\n"
        "🎯 Where to deliver the order?\n\n"
        "👤 Enter your first name:",
        reply_markup=back_to_menu_keyboard()
    )

@router.message(OrderStates.entering_first_name)
async def process_first_name(message: Message, state: FSMContext):
    """Process first name"""
    
    first_name = message.text.strip()
    
    if len(first_name) < 2:
        await message.answer("❌ Please write correct name.")
        return
    
    await state.update_data(first_name=first_name)
    await state.set_state(OrderStates.entering_last_name)
    
    await message.answer("👤 Enter your last name:")

@router.message(OrderStates.entering_last_name)
async def process_last_name(message: Message, state: FSMContext):
    """Process last name"""
    
    last_name = message.text.strip()
    
    if len(last_name) < 2:
        await message.answer("❌ Please write correct lastname.")
        return
    
    await state.update_data(last_name=last_name)
    await state.set_state(OrderStates.entering_street)
    
    await message.answer("🏠 Enter street address (e.g.: 123 Main Street):")

@router.message(OrderStates.entering_street)
async def process_street(message: Message, state: FSMContext):
    """Process street address"""
    
    street = message.text.strip()
    
    if len(street) < 5:
        await message.answer("❌ Пожалуйста, введите корректный адрес улицы.")
        return
    
    await state.update_data(street=street)
    await state.set_state(OrderStates.entering_city)
    
    await message.answer("🏙️ Enter city:")

@router.message(OrderStates.entering_city)
async def process_city(message: Message, state: FSMContext):
    """Process city"""
    
    city = message.text.strip()
    
    if len(city) < 2:
        await message.answer("❌ Пожалуйста, введите корректное название города.")
        return
    
    await state.update_data(city=city)
    await state.set_state(OrderStates.entering_state)
    
    await message.answer("🗺️ Enter state (e.g.: CA, NY, TX):")

@router.message(OrderStates.entering_state)
async def process_us_state(message: Message, state: FSMContext):
    """Process state"""
    
    us_state = message.text.strip().upper()
    
    if len(us_state) < 2:
        await message.answer("❌ Пожалуйста, введите корректное сокращение штата (например: CA, NY, TX).")
        return
    
    await state.update_data(us_state=us_state)
    await state.set_state(OrderStates.entering_zip_code)
    
    await message.answer("📮 Enter ZIP code:")

@router.message(OrderStates.entering_zip_code)
async def process_zip_code(message: Message, state: FSMContext):
    """Process ZIP code"""
    
    zip_code = message.text.strip()
    
    if not zip_code.isdigit() or len(zip_code) != 5:
        await message.answer("❌ Пожалуйста, введите корректный ZIP код (5 цифр).")
        return
    
    await state.update_data(zip_code=zip_code)
    await state.set_state(OrderStates.entering_phone)
    
    await message.answer(
        "📱 Enter phone number (optional):\n"
        "Example: +1234567890",
        reply_markup=skip_field_keyboard()
    )

@router.callback_query(F.data == "skip_field", OrderStates.entering_phone)
async def skip_phone(callback: CallbackQuery, state: FSMContext):
    """Skip phone number"""
    await state.update_data(phone=None)
    await state.set_state(OrderStates.entering_apartment)
    
    await callback.message.answer(
        "🏢 Enter apartment/office number (optional):\n"
        "Example: Apt 5B, Suite 200",
        reply_markup=skip_field_keyboard()
    )
    await callback.answer()

@router.message(OrderStates.entering_phone)
async def process_phone(message: Message, state: FSMContext):
    """Process phone number (optional)"""
    
    phone = message.text.strip()
    
    if phone.lower() in ['пропустить', 'skip', '-']:
        phone = None
    elif phone and (not phone.startswith('+') or len(phone) < 10):
        await message.answer("❌ Пожалуйста, введите корректный номер телефона или 'пропустить'.")
        return
    
    await state.update_data(phone=phone)
    await state.set_state(OrderStates.entering_apartment)
    
    await message.answer(
        "🏢 Enter apartment/office number (optional):\n"
        "Example: Apt 5B, Suite 200",
        reply_markup=skip_field_keyboard()
    )

@router.callback_query(F.data == "skip_field", OrderStates.entering_apartment)
async def skip_apartment(callback: CallbackQuery, state: FSMContext):
    """Skip apartment/office number"""
    await state.update_data(apartment=None)
    await state.set_state(OrderStates.entering_company)
    
    await callback.message.answer(
        "🏢 Enter company name (optional):",
        reply_markup=skip_field_keyboard()
    )
    await callback.answer()

@router.message(OrderStates.entering_apartment)
async def process_apartment(message: Message, state: FSMContext):
    """Process apartment/office number (optional)"""
    
    apartment = message.text.strip()
    
    if apartment.lower() in ['пропустить', 'skip', '-']:
        apartment = None
    
    await state.update_data(apartment=apartment)
    await state.set_state(OrderStates.entering_company)
    
    await message.answer(
        "🏢 Enter company name (optional):",
        reply_markup=skip_field_keyboard()
    )

@router.callback_query(F.data == "skip_field", OrderStates.entering_company)
async def skip_company(callback: CallbackQuery, state: FSMContext):
    """Skip company name"""
    await state.update_data(company=None)
    await state.set_state(OrderStates.selecting_payment)
    
    user_id = callback.from_user.id
    cart_items = cart_service.get_cart(user_id)
    cart_total = cart_service.get_cart_total(user_id)
    
    order_data = await state.get_data()
    
    confirmation_text = format_order_confirmation(cart_items, cart_total, order_data)
    
    await callback.message.answer(
        confirmation_text,
        reply_markup=checkout_keyboard()
    )
    await callback.answer()

@router.message(OrderStates.entering_company)
async def process_company(message: Message, state: FSMContext):
    """Process company name (optional)"""
    
    company = message.text.strip()
    
    if company.lower() in ['пропустить', 'skip', '-']:
        company = None
    
    await state.update_data(company=company)
    await state.set_state(OrderStates.selecting_payment)
    
    user_id = message.from_user.id
    cart_items = cart_service.get_cart(user_id)
    cart_total = cart_service.get_cart_total(user_id)
    
    order_data = await state.get_data()
    
    confirmation_text = format_order_confirmation(cart_items, cart_total, order_data)
    
    await message.answer(
        confirmation_text,
        reply_markup=checkout_keyboard()
    )

@router.callback_query(F.data.startswith("payment:"), OrderStates.selecting_payment)
async def select_payment_method(callback: CallbackQuery, state: FSMContext):
    """Select payment method"""
    
    payment_method = callback.data.split(":")[1]
    await state.update_data(payment_method=payment_method)
    
    user_id = callback.from_user.id
    cart_items = cart_service.get_cart(user_id)
    cart_total = cart_service.get_cart_total(user_id)
    order_data = await state.get_data()
    
    # Recalculate with discount if there's a promocode
    final_total = cart_total
    discount_text = ""
    
    if order_data.get('promocode'):
        discount_type = order_data.get('discount_type', 'percentage')
        discount_value = order_data.get('discount_value', 0)
        logger.info(f"Payment method selection - discount_type: {discount_type}, discount_value: {discount_value}")
        
        if discount_type == 'fixed':
            discount_amount = min(float(discount_value), cart_total)
            promo_text = f"🎫 <b>Промокод:</b> {order_data['promocode']} (-${discount_amount:.2f})\n"
        else:  # percentage
            discount_amount = cart_total * (float(discount_value) / 100)
            promo_text = f"🎫 <b>Промокод:</b> {order_data['promocode']} (-{discount_value}%)\n"
        
        final_total = cart_total - discount_amount
        discount_text = (
            f"{promo_text}"
            f"💰 <b>Скидка:</b> -${discount_amount:.2f}\n"
            f"💵 <b>К оплате:</b> ${final_total:.2f}\n\n"
        )
    
    # Final order confirmation
    confirmation_text = (
        "✅ <b>Confirming order</b>\n\n"
        f"{format_order_confirmation(cart_items, cart_total, order_data)}\n\n"
        f"{discount_text}"
        f"💳 <b>Payment method:</b> {payment_method.upper()}\n\n"
        "Все данные корректны?"
    )
    
    await state.set_state(OrderStates.confirming_order)
    
    await callback.message.edit_text(
        confirmation_text,
        reply_markup=order_confirmation_keyboard()
    )

async def handle_zelle_payment(callback: CallbackQuery, order_id: int, total_amount: float, user_id: int):
    """Handle Zelle payment"""
    
    # Check if user has Zelle credentials
    async with api_client as client:
        zelle_data = await client.get_user_zelle(user_id)
    
    # Check if user has assigned Zelle email
    if zelle_data.get('has_zelle') and zelle_data.get('zelle_email'):
        # User has assigned Zelle email
        payment_text = (
            f"✅ <b>Order #{order_id} created!</b>\n\n"
            f"💵 <b>Zelle Payment</b>\n"
            f"💰 Amount to pay: <b>${total_amount}</b>\n\n"
            f"📋 <b>Payment details:</b>\n"
            f"📧 Email: <code>{zelle_data.get('zelle_email')}</code>\n\n"
            f"📝 <b>If comment is required, please write:</b>\n"
            f"<code>service</code>\n\n"
            f"🕐 After payment we will process your order."
        )
    else:
        # User doesn't have assigned Zelle email
        payment_text = (
            f"✅ <b>Order #{order_id} created!</b>\n\n"
            f"💵 <b>Zelle Payment</b>\n"
            f"💰 Amount to pay: <b>${total_amount}</b>\n\n"
            f"⏳ <b>Please wait, we will send you payment details soon!</b>\n\n"
            f"📱 We will prepare personalized Zelle details for your order.\n"
            f"🕐 This usually takes a few minutes."
        )
    
    await callback.message.edit_text(
        payment_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📦 Мои заказы", callback_data="my_orders")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
    )

async def send_crypto_payment_info(callback: CallbackQuery, order_id: int, total_amount: float):
    """Send cryptocurrency payment information"""
    
    payment_text = (
        f"✅ <b>Заказ #{order_id} создан!</b>\n\n"
        f"💎 <b>Оплата криптовалютой</b>\n"
        f"💰 Сумма к оплате: <b>${total_amount}</b>\n\n"
        f"🔗 Для оплаты перейдите по ссылке:\n"
        f"👆 Ссылка будет сгенерирована автоматически\n\n"
        f"⏰ После оплаты средства поступят автоматически.\n"
        f"📱 Вы получите уведомление о подтверждении платежа."
    )
    
    await callback.message.edit_text(
        payment_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить", url=f"https://payment-link-for-order-{order_id}")],
            [InlineKeyboardButton(text="📦 Мои заказы", callback_data="my_orders")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
    )

@router.callback_query(F.data == "enter_promocode", OrderStates.confirming_order)
async def enter_promocode(callback: CallbackQuery, state: FSMContext):
    """Enter promocode"""
    
    await state.set_state(OrderStates.entering_promocode_code)
    
    await callback.message.edit_text(
        "🎫 <b>Введите промокод</b>\n\n"
        "Отправьте код для получения скидки:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад к заказу", callback_data="back_to_confirmation")]
        ])
    )

@router.message(OrderStates.entering_promocode_code)
async def process_promocode(message: Message, state: FSMContext):
    """Process promocode"""
    
    promocode = message.text.strip().upper()
    
    # Check promocode via API
    async with api_client as client:
        result = await client.check_promocode(promocode)
    
    # Log full API response for debugging
    logger.info(f"Promocode API response for {promocode}: {result}")
    
    if result.get('valid'):
        # Get discount data
        discount_type = result.get('discount_type', 'percentage')
        discount_value = float(result.get('discount_value', 0))
        
        # Save promocode and discount data
        await state.update_data(
            promocode=promocode,
            discount_type=discount_type,
            discount_value=discount_value
        )
        
        # Format message depending on discount type
        if discount_type == 'fixed':
            await message.answer(
                f"✅ Promocode <b>{promocode}</b> применен!\n"
                f"💰 Fix Discount: ${discount_value}"
            )
        else:  # percentage
            await message.answer(
                f"✅ Promocode <b>{promocode}</b> применен!\n"
                f"💰 Discount: {discount_value}%"
            )
        
        # Return to order confirmation with recalculation
        await state.set_state(OrderStates.confirming_order)
        
        user_id = message.from_user.id
        cart_items = cart_service.get_cart(user_id)
        cart_total = cart_service.get_cart_total(user_id)
        order_data = await state.get_data()
        
        # Recalculate with discount
        if discount_type == 'fixed':
            discount_amount = min(float(discount_value), cart_total)
            discount_text = f"🎫 <b>Promorode:</b> {promocode} (-${discount_amount:.2f})\n"
        else:  # percentage
            discount_amount = cart_total * (float(discount_value) / 100)
            discount_text = f"🎫 <b>Promocode:</b> {promocode} (-{discount_value}%)\n"
        
        final_total = cart_total - discount_amount
        
        confirmation_text = (
            "✅ <b>Подтверждение заказа</b>\n\n"
            f"{format_order_confirmation(cart_items, cart_total, order_data)}\n\n"
            f"{discount_text}"
            f"💰 <b>Скидка:</b> -${discount_amount:.2f}\n"
            f"💵 <b>К оплате:</b> ${final_total:.2f}\n\n"
            "Все данные корректны?"
        )
        
        await message.answer(
            confirmation_text,
            reply_markup=order_confirmation_keyboard()
        )
        
    else:
        await message.answer(
            f"❌ Promocode <b>{promocode}</b> not found."
        )

@router.callback_query(F.data == "back_to_confirmation")
async def back_to_confirmation(callback: CallbackQuery, state: FSMContext):
    """Return to order confirmation"""
    
    await state.set_state(OrderStates.confirming_order)
    
    user_id = callback.from_user.id
    cart_items = cart_service.get_cart(user_id)
    cart_total = cart_service.get_cart_total(user_id)
    order_data = await state.get_data()
    
    confirmation_text = (
        "✅ <b>Подтверждение заказа</b>\n\n"
        f"{format_order_confirmation(cart_items, cart_total, order_data)}\n\n"
        "Все данные корректны?"
    )
    
    await callback.message.edit_text(
        confirmation_text,
        reply_markup=order_confirmation_keyboard()
    )

@router.callback_query(F.data == "confirm_order", OrderStates.confirming_order)
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    """Confirm and create order"""
    
    user_id = callback.from_user.id
    cart_items = cart_service.get_cart(user_id)
    order_data = await state.get_data()
    
    # Prepare data for API
    api_order_data = {
        'telegram_user_id': user_id,
        'products': [
            {
                'id': item['id'],
                'quantity': item['quantity']
            }
            for item in cart_items
        ],
        'payment_method': order_data['payment_method'],
        'shipping_address': {
            'first_name': order_data['first_name'],
            'last_name': order_data['last_name'],
            'street': order_data['street'],
            'city': order_data['city'],
            'state': order_data['us_state'],
            'zip_code': order_data['zip_code'],
            'country': 'USA',
            'phone': order_data.get('phone'),
            'apartment': order_data.get('apartment'),
            'company': order_data.get('company')
        }
    }
    
    # Add promocode if exists
    if order_data.get('promocode'):
        api_order_data['promocode'] = order_data['promocode']
    
    # Create order via API
    async with api_client as client:
        result = await client.create_order(api_order_data)
    
    if not result or 'order_id' not in result:
        await callback.message.edit_text(
            "❌ Ошибка при создании заказа. Попробуйте позже.",
            reply_markup=back_to_menu_keyboard()
        )
        return
    
    order_id = result['order_id']
    
    # Track order creation for reminders via Laravel API
    try:
        async with api_client as client:
            await client.track_user_activity(user_id, 'order_created', {
                'order_id': order_id,
                'payment_method': order_data['payment_method'], 
                'total_amount': result['total_amount']
            })
    except Exception as e:
        logger.error(f"Failed to track order creation: {e}")
    
    # Send notification to admins about new order
    logger.info(f"Preparing admin notification for order {order_id}")
    try:
        user_info = {
            'telegram_id': user_id,
            'first_name': callback.from_user.first_name,
            'last_name': callback.from_user.last_name,
            'username': callback.from_user.username
        }
        
        notification_data = {
            'order_id': order_id,
            'total_amount': result.get('total_amount', 0),
            'payment_method': order_data['payment_method'],
            'products': [
                {
                    'id': item['id'],
                    'name': item['name'], 
                    'quantity': item['quantity']
                }
                for item in cart_items
            ],
            'shipping_address': {
                'first_name': order_data['first_name'],
                'last_name': order_data['last_name'],
                'street': order_data['street'],
                'city': order_data['city'],
                'state': order_data['us_state'],
                'zip_code': order_data['zip_code'],
                'phone': order_data.get('phone'),
                'apartment': order_data.get('apartment')
            },
            'promocode': order_data.get('promocode'),
            'zelle_assigned': result.get('zelle_assigned', False)
        }
        
        await notify_admins_new_order(notification_data, user_info, callback.bot)
        logger.info(f"Admin notification sent for order {order_id}")
    except Exception as e:
        logger.error(f"Failed to send admin notification for order {order_id}: {e}")
    
    # Clear cart and state
    cart_service.clear_cart(user_id)
    await state.clear()
    
    # Send confirmation depending on payment method
    if order_data['payment_method'] == 'zelle':
        await handle_zelle_payment(callback, order_id, result['total_amount'], user_id)
    else:  # nowpayments
        await send_crypto_payment_info(callback, order_id, result['total_amount'])