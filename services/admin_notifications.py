import logging
from typing import Dict, List
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import settings

logger = logging.getLogger(__name__)

async def notify_admins_new_order(order_data: Dict, user_data: Dict, bot: Bot = None):
    """Send notification to admins about new order"""
    
    # Try to get admin_ids from multiple sources
    admin_ids = settings.admin_ids
    logger.info(f"Admin IDs from config: {admin_ids}")
    
    # Если не найдены в настройках, попробуем напрямую из переменной окружения
    if not admin_ids:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        admin_ids_str = os.getenv('ADMIN_IDS', '')
        logger.info(f"Admin IDs from env directly: {repr(admin_ids_str)}")
        
        if admin_ids_str.strip():
            try:
                admin_ids = [int(x.strip()) for x in admin_ids_str.split(',') if x.strip()]
                logger.info(f"Parsed admin IDs from env: {admin_ids}")
            except ValueError as e:
                logger.error(f"Failed to parse admin IDs from env: {e}")
                admin_ids = []
    
    if not admin_ids:
        logger.warning("No admin IDs configured for notifications")
        return
    
    # Создаем новый Bot если не передан
    if bot is None:
        bot = Bot(token=settings.bot_token)
        should_close_session = True
    else:
        should_close_session = False
    
    try:
        # Форматируем сообщение уведомления
        notification_text = format_admin_notification(order_data, user_data)
        
        # Создаем клавиатуру с быстрыми действиями
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 Назначить Zelle", 
                    url=f"http://127.0.0.1:8000/admin/orders/{order_data['order_id']}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Все заказы", 
                    url="http://127.0.0.1:8000/admin/orders"
                )
            ]
        ])
        
        # Отправляем уведомление каждому админу
        for admin_id in admin_ids:
            try:
                logger.info(f"Attempting to send notification to admin {admin_id}")
                result = await bot.send_message(
                    chat_id=admin_id,
                    text=notification_text,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
                logger.info(f"Admin notification sent successfully to {admin_id}, message ID: {result.message_id}")
            except Exception as e:
                logger.error(f"Failed to send notification to admin {admin_id}: {e}")
        
        if should_close_session and bot.session:
            await bot.session.close()
        
    except Exception as e:
        logger.error(f"Error sending admin notifications: {e}")
        if should_close_session and bot.session:
            await bot.session.close()

def format_admin_notification(order_data: Dict, user_data: Dict) -> str:
    """Format notification for admin"""
    
    # Emoji for payment statuses
    payment_emoji = {
        'zelle': '💳',
        'crypto': '💎',
        'nowpayments': '💎'
    }
    
    message = "🔔 <b>НОВЫЙ ЗАКАЗ!</b>\n\n"
    
    # Основная информация о заказе
    message += f"📦 <b>Заказ #{order_data.get('order_id', 'N/A')}</b>\n"
    message += f"💰 <b>Сумма:</b> ${order_data.get('total_amount', 0)}\n"
    
    payment_method = order_data.get('payment_method', 'unknown')
    emoji = payment_emoji.get(payment_method, '💳')
    message += f"{emoji} <b>Оплата:</b> {payment_method.upper()}\n\n"
    
    # Информация о пользователе
    message += "👤 <b>Клиент:</b>\n"
    message += f"🆔 Telegram ID: <code>{user_data.get('telegram_id', 'N/A')}</code>\n"
    
    if user_data.get('first_name'):
        message += f"👤 Имя: {user_data['first_name']}"
        if user_data.get('last_name'):
            message += f" {user_data['last_name']}"
        message += "\n"
    
    if user_data.get('username'):
        message += f"📱 Username: @{user_data['username']}\n"
    
    # Товары в заказе
    products = order_data.get('products', [])
    if products:
        message += "\n🛍️ <b>Товары:</b>\n"
        for product in products:
            name = product.get('name', 'Неизвестный товар')
            quantity = product.get('quantity', 1)
            message += f"• {name} × {quantity}\n"
    
    # Адрес доставки
    shipping = order_data.get('shipping_address', {})
    if shipping:
        message += "\n📍 <b>Адрес доставки:</b>\n"
        
        # Имя получателя
        if shipping.get('first_name') or shipping.get('last_name'):
            message += f"👤 {shipping.get('first_name', '')} {shipping.get('last_name', '')}\n"
        
        # Адрес
        street = shipping.get('street', '')
        apartment = shipping.get('apartment', '')
        if street:
            address_line = street
            if apartment:
                address_line += f", {apartment}"
            message += f"🏠 {address_line}\n"
        
        # Город, штат, ZIP
        city = shipping.get('city', '')
        state = shipping.get('state', '')
        zip_code = shipping.get('zip_code', '')
        if city or state or zip_code:
            location = f"{city}, {state} {zip_code}".strip(', ')
            message += f"🌍 {location}\n"
        
        # Телефон
        phone = shipping.get('phone', '')
        if phone:
            message += f"📞 {phone}\n"
    
    # Промокод
    promocode = order_data.get('promocode')
    if promocode:
        message += f"\n🎫 <b>Промокод:</b> {promocode}\n"
    
    # Статус Zelle
    if payment_method == 'zelle':
        zelle_assigned = order_data.get('zelle_assigned', False)
        if zelle_assigned:
            message += "\n✅ <b>Zelle назначен</b>"
        else:
            message += "\n⚠️ <b>Требуется назначить Zelle!</b>"
    
    message += "\n\n⏰ <b>Требует внимания!</b>"
    
    return message

async def send_support_message(support_data: Dict, user_data: Dict, bot: Bot = None):
    """Отправка сообщения поддержки администратору"""
    
    admin_ids = settings.admin_ids
    logger.info(f"Sending support message to admin IDs: {admin_ids}")
    
    # Если не найдены в настройках, попробуем напрямую из переменной окружения
    if not admin_ids:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        admin_ids_str = os.getenv('ADMIN_IDS', '')
        
        if admin_ids_str.strip():
            try:
                admin_ids = [int(x.strip()) for x in admin_ids_str.split(',') if x.strip()]
            except ValueError as e:
                logger.error(f"Failed to parse admin IDs from env: {e}")
                admin_ids = []
    
    if not admin_ids:
        logger.warning("No admin IDs configured for support messages")
        return
    
    # Создаем новый Bot если не передан
    if bot is None:
        bot = Bot(token=settings.bot_token)
        should_close_session = True
    else:
        should_close_session = False
    
    try:
        # Форматируем сообщение поддержки
        notification_text = format_support_notification(support_data, user_data)
        
        # Отправляем уведомление каждому админу
        for admin_id in admin_ids:
            try:
                logger.info(f"Attempting to send support message to admin {admin_id}")
                result = await bot.send_message(
                    chat_id=admin_id,
                    text=notification_text,
                    parse_mode="HTML"
                )
                logger.info(f"Support message sent successfully to {admin_id}, message ID: {result.message_id}")
            except Exception as e:
                logger.error(f"Failed to send support message to admin {admin_id}: {e}")
        
        if should_close_session and bot.session:
            await bot.session.close()
        
    except Exception as e:
        logger.error(f"Error sending support messages: {e}")
        if should_close_session and bot.session:
            await bot.session.close()

def format_support_notification(support_data: Dict, user_data: Dict) -> str:
    """Форматирование уведомления о сообщении поддержки"""
    
    message = "💬 <b>НОВОЕ ОБРАЩЕНИЕ В ПОДДЕРЖКУ!</b>\n\n"
    
    # Информация о пользователе
    message += "👤 <b>От пользователя:</b>\n"
    message += f"🆔 Telegram ID: <code>{user_data.get('telegram_id', 'N/A')}</code>\n"
    
    if user_data.get('first_name'):
        message += f"👤 Имя: {user_data['first_name']}"
        if user_data.get('last_name'):
            message += f" {user_data['last_name']}"
        message += "\n"
    
    if user_data.get('username'):
        message += f"📱 Username: @{user_data['username']}\n"
    
    # Тема и сообщение
    message += f"\n📋 <b>Тема:</b> {support_data.get('subject', 'Без темы')}\n\n"
    message += f"💬 <b>Сообщение:</b>\n{support_data.get('message', 'Пустое сообщение')}\n\n"
    
    message += "⏰ <b>Требует ответа!</b>"
    
    return message