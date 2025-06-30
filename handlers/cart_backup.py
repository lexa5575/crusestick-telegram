import logging
from typing import Dict
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from config import settings
from keyboards.inline import (
    cart_keyboard, cart_item_keyboard, checkout_keyboard, 
    order_confirmation_keyboard, back_to_menu_keyboard
)
from services.cart_service import cart_service
from services.api_client import api_client
from states.order_states import OrderStates
from utils.formatters import format_cart_message, format_order_confirmation

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data.startswith("add_to_cart:"))
async def add_product_to_cart(callback: CallbackQuery):
    """Добавить товар в корзину"""
    
    try:
        logger.info(f"Add to cart callback received: {callback.data}")
        
        product_id = int(callback.data.split(":")[1])
        user_id = callback.from_user.id
        
        logger.info(f"Adding product {product_id} to cart for user {user_id}")
        
        # Получаем данные товара из API
        async with api_client as client:
            products = await client.get_products()
            product = next((p for p in products if p['id'] == product_id), None)
        
        if not product:
            logger.warning(f"Product {product_id} not found")
            await callback.answer("Товар не найден", show_alert=True)
            return
        
        # Добавляем в корзину
        cart_service.add_to_cart(user_id, product)
        logger.info(f"Product {product['name']} added to cart for user {user_id}")
        
        await callback.answer(f"✅ {product['name']} добавлен в корзину!")
        
    except Exception as e:
        logger.error(f"Error adding product to cart: {e}")
        await callback.answer("Ошибка при добавлении товара", show_alert=True)

@router.callback_query(F.data == "cart")
async def show_cart(callback: CallbackQuery, state: FSMContext):
    """Показать корзину"""
    
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
    """Редактировать товар в корзине"""
    
    product_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    cart_items = cart_service.get_cart(user_id)
    item = next((item for item in cart_items if item['id'] == product_id), None)
    
    if not item:
        await callback.answer("Товар не найден в корзине", show_alert=True)
        return
    
    message_text = (
        f"📝 <b>{item['name']}</b>\n\n"
        f"💰 Цена: ${item['price']}\n"
        f"📦 Количество: {item['quantity']}\n"
        f"💵 Сумма: ${item['total']}\n\n"
        "Изменить количество:"
    )
    
    await callback.message.edit_text(
        message_text,
        reply_markup=cart_item_keyboard(product_id, item['quantity'])
    )

@router.callback_query(F.data.startswith("cart_quantity:"))
async def update_cart_quantity(callback: CallbackQuery):
    """Обновить количество товара в корзине"""
    
    _, product_id, new_quantity = callback.data.split(":")
    product_id = int(product_id)
    new_quantity = int(new_quantity)
    user_id = callback.from_user.id
    
    if new_quantity <= 0:
        cart_service.remove_from_cart(user_id, product_id)
        await callback.answer("Товар удален из корзины")
        await show_cart(callback, None)
        return
    
    cart_service.update_quantity(user_id, product_id, new_quantity)
    
    # Обновляем сообщение
    cart_items = cart_service.get_cart(user_id)
    item = next((item for item in cart_items if item['id'] == product_id), None)
    
    if item:
        message_text = (
            f"📝 <b>{item['name']}</b>\n\n"
            f"💰 Цена: ${item['price']}\n"
            f"📦 Количество: {item['quantity']}\n"
            f"💵 Сумма: ${item['total']}\n\n"
            "Изменить количество:"
        )
        
        await callback.message.edit_text(
            message_text,
            reply_markup=cart_item_keyboard(product_id, item['quantity'])
        )
    
    await callback.answer(f"Количество изменено на {new_quantity}")

@router.callback_query(F.data.startswith("remove_from_cart:"))
async def remove_from_cart(callback: CallbackQuery):
    """Удалить товар из корзины"""
    
    product_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    cart_service.remove_from_cart(user_id, product_id)
    
    await callback.answer("Товар удален из корзины")
    await show_cart(callback, None)

@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery):
    """Очистить корзину"""
    
    user_id = callback.from_user.id
    cart_service.clear_cart(user_id)
    
    await callback.answer("Корзина очищена")
    await show_cart(callback, None)

@router.callback_query(F.data == "checkout")
async def start_checkout(callback: CallbackQuery, state: FSMContext):
    """Начать оформление заказа"""
    
    user_id = callback.from_user.id
    cart_items = cart_service.get_cart(user_id)
    
    if not cart_items:
        await callback.answer("Корзина пуста", show_alert=True)
        return
    
    await state.set_state(OrderStates.entering_contact)
    
    await callback.message.edit_text(
        "📞 <b>Оформление заказа</b>\n\n"
        "Пожалуйста, отправьте ваш номер телефона для связи.\n"
        "Например: +1234567890",
        reply_markup=back_to_menu_keyboard()
    )

@router.message(OrderStates.entering_contact)
async def process_contact(message: Message, state: FSMContext):
    """Обработка контактной информации"""
    
    phone = message.text.strip()
    
    # Простая валидация номера телефона
    if not phone.startswith('+') or len(phone) < 10:
        await message.answer(
            "❌ Пожалуйста, введите корректный номер телефона.\n"
            "Например: +1234567890"
        )
        return
    
    # Сохраняем номер телефона в состоянии
    await state.update_data(phone=phone)
    await state.set_state(OrderStates.entering_address)
    
    await message.answer(
        "📍 <b>Адрес доставки</b>\n\n"
        "Пожалуйста, введите полный адрес доставки:\n"
        "• Имя получателя\n"
        "• Адрес\n"
        "• Город, штат, ZIP код\n"
        "• Страна"
    )

@router.message(OrderStates.entering_address)
async def process_address(message: Message, state: FSMContext):
    """Обработка адреса доставки"""
    
    address = message.text.strip()
    
    if len(address) < 20:
        await message.answer(
            "❌ Пожалуйста, введите полный адрес доставки.\n"
            "Адрес должен содержать все необходимые данные."
        )
        return
    
    # Сохраняем адрес
    await state.update_data(address=address)
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
    """Выбор способа оплаты"""
    
    payment_method = callback.data.split(":")[1]
    await state.update_data(payment_method=payment_method)
    
    user_id = callback.from_user.id
    cart_items = cart_service.get_cart(user_id)
    cart_total = cart_service.get_cart_total(user_id)
    order_data = await state.get_data()
    
    # Пересчитываем с учетом скидки, если есть промокод
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
    
    # Финальное подтверждение заказа
    confirmation_text = (
        "✅ <b>Подтверждение заказа</b>\n\n"
        f"{format_order_confirmation(cart_items, cart_total, order_data)}\n\n"
        f"{discount_text}"
        f"💳 <b>Способ оплаты:</b> {payment_method.upper()}\n\n"
        "Все данные корректны?"
    )
    
    await state.set_state(OrderStates.confirming_order)
    
    await callback.message.edit_text(
        confirmation_text,
        reply_markup=order_confirmation_keyboard()
    )

async def handle_zelle_payment(callback: CallbackQuery, order_id: int, total_amount: float, user_id: int):
    """Обработка оплаты через Zelle с проверкой настроенных реквизитов"""
    
    # Проверяем, есть ли у пользователя настроенные Zelle реквизиты
    async with api_client as client:
        zelle_data = await client.get_user_zelle(user_id)
    
    if zelle_data.get('configured', False):
        # У пользователя есть настроенные реквизиты - отправляем их
        await send_personalized_zelle_info(callback, order_id, total_amount, zelle_data)
    else:
        # Реквизиты не настроены - отправляем сообщение ожидания и уведомляем админов
        await send_waiting_message(callback, order_id, total_amount)
        await notify_admins_new_order(callback.from_user, order_id)

async def send_waiting_message(callback: CallbackQuery, order_id: int, total_amount: float):
    """Отправка сообщения ожидания реквизитов от менеджера"""
    
    waiting_text = (
        f"✅ <b>Заказ #{order_id} создан!</b>\n\n"
        f"💵 <b>Сумма к оплате: ${total_amount}</b>\n\n"
        f"⏳ <b>Заказ создан, ждите реквизиты от менеджера</b>\n\n"
        f"📱 Мы подготовим персональные реквизиты Zelle для вашего заказа.\n"
        f"🕐 Обычно это занимает несколько минут."
    )
    
    await callback.message.edit_text(
        waiting_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📦 Мои заказы", callback_data="my_orders")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
    )

async def send_personalized_zelle_info(callback: CallbackQuery, order_id: int, total_amount: float, zelle_data: Dict):
    """Отправка персональных Zelle реквизитов пользователя"""
    
    payment_text = (
        f"✅ <b>Заказ #{order_id} создан!</b>\n\n"
        f"💵 <b>Оплата через Zelle</b>\n"
        f"💰 Сумма к оплате: <b>${total_amount}</b>\n\n"
        f"📋 <b>Ваши персональные реквизиты для перевода:</b>\n"
        f"📧 Email: <code>{zelle_data.get('email', 'Не указан')}</code>\n"
        f"📱 Phone: <code>{zelle_data.get('phone', 'Не указан')}</code>\n"
        f"👤 Name: <code>{zelle_data.get('name', 'Не указан')}</code>\n\n"
        f"📝 <b>В комментарии к переводу укажите:</b>\n"
        f"<code>Order #{order_id}</code>\n\n"
        f"⚠️ После оплаты отправьте скриншот чека для подтверждения.\n\n"
        f"🕐 Заказ будет обработан после подтверждения оплаты."
    )
    
    await callback.message.edit_text(
        payment_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📸 Отправить чек", callback_data=f"upload_receipt:{order_id}")],
            [InlineKeyboardButton(text="📦 Мои заказы", callback_data="my_orders")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
    )

async def notify_admins_new_order(user, order_id: int):
    """Уведомление админов о новом заказе, требующем настройки Zelle"""
    
    # Получаем список админов из настроек
    admin_ids = getattr(settings, 'admin_ids', [])
    
    if not admin_ids:
        logger.warning("No admin IDs configured for notifications")
        return
    
    # Подготавливаем данные для API уведомления
    notification_data = {
        'order_id': order_id,
        'user_info': {
            'telegram_id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username
        },
        'action_required': 'setup_zelle',
        'message': 'Новый заказ требует настройки персональных Zelle реквизитов'
    }
    
    # Отправляем уведомление через API
    async with api_client as client:
        await client.notify_admin_new_order(notification_data)
    
    logger.info(f"Admin notification sent for order {order_id}, user {user.id}")

@router.callback_query(F.data == "confirm_order", OrderStates.confirming_order)
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    """Подтверждение и создание заказа"""
    
    user_id = callback.from_user.id
    cart_items = cart_service.get_cart(user_id)
    order_data = await state.get_data()
    
    # Подготавливаем данные для API
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
        'customer_notes': f"Phone: {order_data['phone']}",
        'shipping_address': {
            'full_address': order_data['address'],
            'phone': order_data['phone']
        }
    }
    
    # Создаем заказ через API
    async with api_client as client:
        result = await client.create_order(api_order_data)
    
    if not result or 'order_id' not in result:
        await callback.message.edit_text(
            "❌ Ошибка при создании заказа. Попробуйте позже.",
            reply_markup=back_to_menu_keyboard()
        )
        return
    
    order_id = result['order_id']
    
    # Очищаем корзину и состояние
    cart_service.clear_cart(user_id)
    await state.clear()
    
    # Отправляем подтверждение в зависимости от способа оплаты
    if order_data['payment_method'] == 'zelle':
        await handle_zelle_payment(callback, order_id, result['total_amount'], user_id)
    else:  # nowpayments
        await send_crypto_payment_info(callback, order_id, result['total_amount'])

async def send_zelle_payment_info(callback: CallbackQuery, order_id: int, total_amount: float):
    """Отправка информации для оплаты через Zelle"""
    
    payment_text = (
        f"✅ <b>Заказ #{order_id} создан!</b>\n\n"
        f"💵 <b>Оплата через Zelle</b>\n"
        f"💰 Сумма к оплате: <b>${total_amount}</b>\n\n"
        f"📋 <b>Реквизиты для перевода:</b>\n"
        f"📧 Email: your-zelle@email.com\n"
        f"📱 Phone: +1234567890\n"
        f"👤 Name: Your Store Name\n\n"
        f"📝 <b>В комментарии к переводу укажите:</b>\n"
        f"<code>Order #{order_id}</code>\n\n"
        f"⚠️ После оплаты отправьте скриншот чека для подтверждения.\n\n"
        f"🕐 Заказ будет обработан после подтверждения оплаты."
    )
    
    await callback.message.edit_text(
        payment_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📸 Отправить чек", callback_data=f"upload_receipt:{order_id}")],
            [InlineKeyboardButton(text="📦 Мои заказы", callback_data="my_orders")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
    )

async def send_crypto_payment_info(callback: CallbackQuery, order_id: int, total_amount: float):
    """Отправка информации для оплаты через криптовалюты"""
    
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
    """Ввод промокода"""
    
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
    """Обработка промокода"""
    
    promocode = message.text.strip().upper()
    
    # Проверяем промокод через API
    async with api_client as client:
        result = await client.check_promocode(promocode)
    
    # Логируем полный ответ API для отладки
    logger.info(f"Promocode API response for {promocode}: {result}")
    
    if result.get('valid'):
        # Проверяем разные возможные поля для процента скидки
        # Также проверяем data вложенность, которая часто используется в Laravel API
        promocode_data = result.get('data', result)
        
        discount_percent = (
            promocode_data.get('discount_value') or 
            promocode_data.get('discount_percent') or 
            promocode_data.get('discount') or 
            promocode_data.get('percentage') or 
            promocode_data.get('percent') or 
            promocode_data.get('value') or
            result.get('discount_value') or
            result.get('discount_percent') or 
            result.get('discount') or 
            result.get('percentage') or 
            result.get('percent') or 
            result.get('value') or 0
        )
        
        logger.info(f"Extracted discount_percent: {discount_percent} from promocode_data: {promocode_data}")
        
        # Получаем тип скидки
        discount_type = promocode_data.get('discount_type', 'percentage')
        discount_value = float(discount_percent)
        
        # Сохраняем промокод и данные скидки
        await state.update_data(
            promocode=promocode,
            discount_type=discount_type,
            discount_value=discount_value
        )
        
        # Форматируем сообщение в зависимости от типа скидки
        if discount_type == 'fixed':
            await message.answer(
                f"✅ Промокод <b>{promocode}</b> применен!\n"
                f"💰 Фиксированная скидка: ${discount_value}"
            )
        else:  # percentage
            await message.answer(
                f"✅ Промокод <b>{promocode}</b> применен!\n"
                f"💰 Скидка: {discount_value}%"
            )
        
        # Возвращаемся к подтверждению заказа с пересчетом
        await state.set_state(OrderStates.confirming_order)
        
        user_id = message.from_user.id
        cart_items = cart_service.get_cart(user_id)
        cart_total = cart_service.get_cart_total(user_id)
        order_data = await state.get_data()
        
        # Пересчитываем с учетом скидки
        discount_type = order_data.get('discount_type', 'percentage')
        discount_value = order_data.get('discount_value', 0)
        
        if discount_type == 'fixed':
            discount_amount = min(float(discount_value), cart_total)  # Не больше суммы заказа
            discount_text = f"🎫 <b>Промокод:</b> {promocode} (-${discount_amount:.2f})\n"
        else:  # percentage
            discount_amount = cart_total * (float(discount_value) / 100)
            discount_text = f"🎫 <b>Промокод:</b> {promocode} (-{discount_value}%)\n"
        
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
            f"❌ Промокод <b>{promocode}</b> недействителен.\n"
            "Попробуйте другой код или продолжите без скидки."
        )

@router.callback_query(F.data == "back_to_confirmation")
async def back_to_confirmation(callback: CallbackQuery, state: FSMContext):
    """Возврат к подтверждению заказа"""
    
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

async def handle_zelle_payment(callback: CallbackQuery, order_id: int, total_amount: float, user_id: int):
    """Обработка оплаты через Zelle с проверкой настроенных реквизитов"""
    
    # Проверяем, есть ли у пользователя настроенные Zelle реквизиты
    async with api_client as client:
        zelle_data = await client.get_user_zelle(user_id)
    
    if zelle_data.get('configured', False):
        # У пользователя есть настроенные реквизиты - отправляем их
        await send_personalized_zelle_info(callback, order_id, total_amount, zelle_data)
    else:
        # Реквизиты не настроены - отправляем сообщение ожидания и уведомляем админов
        await send_waiting_message(callback, order_id, total_amount)
        await notify_admins_new_order(callback.from_user, order_id)

async def send_waiting_message(callback: CallbackQuery, order_id: int, total_amount: float):
    """Отправка сообщения ожидания реквизитов от менеджера"""
    
    waiting_text = (
        f"✅ <b>Заказ #{order_id} создан!</b>\n\n"
        f"💵 <b>Сумма к оплате: ${total_amount}</b>\n\n"
        f"⏳ <b>Заказ создан, ждите реквизиты от менеджера</b>\n\n"
        f"📱 Мы подготовим персональные реквизиты Zelle для вашего заказа.\n"
        f"🕐 Обычно это занимает несколько минут."
    )
    
    await callback.message.edit_text(
        waiting_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📦 Мои заказы", callback_data="my_orders")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
    )

async def send_personalized_zelle_info(callback: CallbackQuery, order_id: int, total_amount: float, zelle_data: Dict):
    """Отправка персональных Zelle реквизитов пользователя"""
    
    payment_text = (
        f"✅ <b>Заказ #{order_id} создан!</b>\n\n"
        f"💵 <b>Оплата через Zelle</b>\n"
        f"💰 Сумма к оплате: <b>${total_amount}</b>\n\n"
        f"📋 <b>Ваши персональные реквизиты для перевода:</b>\n"
        f"📧 Email: <code>{zelle_data.get('email', 'Не указан')}</code>\n"
        f"📱 Phone: <code>{zelle_data.get('phone', 'Не указан')}</code>\n"
        f"👤 Name: <code>{zelle_data.get('name', 'Не указан')}</code>\n\n"
        f"📝 <b>В комментарии к переводу укажите:</b>\n"
        f"<code>Order #{order_id}</code>\n\n"
        f"⚠️ После оплаты отправьте скриншот чека для подтверждения.\n\n"
        f"🕐 Заказ будет обработан после подтверждения оплаты."
    )
    
    await callback.message.edit_text(
        payment_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📸 Отправить чек", callback_data=f"upload_receipt:{order_id}")],
            [InlineKeyboardButton(text="📦 Мои заказы", callback_data="my_orders")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
    )

async def notify_admins_new_order(user, order_id: int):
    """Уведомление админов о новом заказе, требующем настройки Zelle"""
    
    # Получаем список админов из настроек
    admin_ids = getattr(settings, 'admin_ids', [])
    
    if not admin_ids:
        logger.warning("No admin IDs configured for notifications")
        return
    
    # Подготавливаем данные для API уведомления
    notification_data = {
        'order_id': order_id,
        'user_info': {
            'telegram_id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username
        },
        'action_required': 'setup_zelle',
        'message': 'Новый заказ требует настройки персональных Zelle реквизитов'
    }
    
    # Отправляем уведомление через API
    async with api_client as client:
        await client.notify_admin_new_order(notification_data)
    
    logger.info(f"Admin notification sent for order {order_id}, user {user.id}")