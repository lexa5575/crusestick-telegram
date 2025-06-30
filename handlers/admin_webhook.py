import logging
from aiohttp import web, ClientSession
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import settings
from services.api_client import api_client

logger = logging.getLogger(__name__)

async def send_zelle_to_user(request):
    """Обработчик для отправки Zelle реквизитов пользователю"""
    try:
        data = await request.json()
        telegram_id = data.get('telegram_id')
        message = data.get('message')
        tracking_number = data.get('tracking_number')
        order_id = data.get('order_id')
        
        if not telegram_id or not message:
            return web.json_response({'success': False, 'error': 'Missing required fields'}, status=400)
        
        bot = Bot(token=settings.bot_token)
        
        try:
            await bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📦 My Orders", callback_data="my_orders")],
                    [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")]
                ])
            )
            
            await bot.session.close()
            logger.info(f"Zelle info sent to user {telegram_id}")
            return web.json_response({'success': True})
            
        except Exception as e:
            logger.error(f"Error sending message to user {telegram_id}: {e}")
            if bot.session:
                await bot.session.close()
            return web.json_response({'success': False, 'error': str(e)}, status=500)
            
    except Exception as e:
        logger.error(f"Error processing zelle request: {e}")
        return web.json_response({'success': False, 'error': str(e)}, status=500)

async def send_tracking_to_user(request):
    """Обработчик для отправки трекинг номера пользователю"""
    try:
        data = await request.json()
        telegram_id = data.get('telegram_id')
        message = data.get('message')
        tracking_number = data.get('tracking_number')
        order_id = data.get('order_id')
        
        if not telegram_id or not message:
            return web.json_response({'success': False, 'error': 'Missing required fields'}, status=400)
        
        bot = Bot(token=settings.bot_token)
        
        try:
            # Создаем клавиатуру с кнопкой отслеживания
            keyboard = []
            if tracking_number:
                keyboard.append([
                    InlineKeyboardButton(
                        text="📦 Chek via USPS", 
                        url=f"https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking_number}"
                    )
                ])
            
            keyboard.extend([
                [InlineKeyboardButton(text="📦 My Orders", callback_data="my_orders")],
                [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")]
            ])
            
            await bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
            
            # Track order completion (tracking sent = order completed)
            if order_id:
                try:
                    async with api_client as client:
                        await client.track_user_activity(telegram_id, 'order_completed', {
                            'order_id': order_id
                        })
                except Exception as e:
                    logger.error(f"Failed to track order completion: {e}")
            
            await bot.session.close()
            logger.info(f"Tracking info sent to user {telegram_id}")
            return web.json_response({'success': True})
            
        except Exception as e:
            logger.error(f"Error sending tracking to user {telegram_id}: {e}")
            if bot.session:
                await bot.session.close()
            return web.json_response({'success': False, 'error': str(e)}, status=500)
            
    except Exception as e:
        logger.error(f"Error processing tracking request: {e}")
        return web.json_response({'success': False, 'error': str(e)}, status=500)

async def send_reminder_to_user(request):
    """Обработчик для отправки напоминаний от Laravel"""
    try:
        data = await request.json()
        telegram_id = data.get('telegram_id')
        message = data.get('message')
        reminder_type = data.get('reminder_type')
        
        if not telegram_id or not message:
            return web.json_response({'success': False, 'error': 'Missing required fields'}, status=400)
        
        bot = Bot(token=settings.bot_token)
        
        try:
            # Import here to avoid circular imports
            from keyboards.inline import main_menu_keyboard
            
            await bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode="HTML",
                reply_markup=main_menu_keyboard()
            )
            
            await bot.session.close()
            logger.info(f"Reminder ({reminder_type}) sent to user {telegram_id}")
            return web.json_response({'success': True})
            
        except Exception as e:
            logger.error(f"Error sending reminder to user {telegram_id}: {e}")
            if bot.session:
                await bot.session.close()
            return web.json_response({'success': False, 'error': str(e)}, status=500)
            
    except Exception as e:
        logger.error(f"Error processing reminder request: {e}")
        return web.json_response({'success': False, 'error': str(e)}, status=500)

def create_admin_app():
    """Создание HTTP приложения для админских команд"""
    app = web.Application()
    
    # Добавляем маршруты
    app.router.add_post('/admin/zelle', send_zelle_to_user)
    app.router.add_post('/admin/tracking', send_tracking_to_user)
    app.router.add_post('/admin/reminder', send_reminder_to_user)
    
    return app