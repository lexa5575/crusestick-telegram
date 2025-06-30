import logging
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from keyboards.inline import get_main_menu
from services.api_client import api_client
from datetime import datetime

router = Router()
logger = logging.getLogger(__name__)

@router.message(CommandStart())
async def start_handler(message: types.Message):
    """Handler for /start command"""
    user = message.from_user
    
    # Sync with Laravel API
    await sync_user_with_api(user)
    
    await message.answer(
        f"👋 Welcome, {user.first_name}!\n\n"
        "🛍️ Our store offers a wide range of products.\n"
        "Choose an action from the menu below:",
        reply_markup=get_main_menu()
    )

@router.callback_query(F.data.in_(["back_to_main", "main_menu"]))
async def back_to_main_handler(callback: CallbackQuery, state: FSMContext = None):
    """Return to main menu"""
    if state:
        await state.clear()
    
    await callback.message.edit_text(
        f"👋 Welcome, {callback.from_user.first_name}!\n\n"
        "🛍️ Our store offers a wide range of products.\n"
        "Choose an action from the menu below:",
        reply_markup=get_main_menu()
    )
    await callback.answer()

async def sync_user_with_api(user: types.User):
    """Sync user with Laravel API"""
    try:
        async with api_client as client:
            user_data = {
                'telegram_id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'language_code': user.language_code,
            }
            
            await client.create_or_update_user(user_data)
            logger.info(f"User {user.id} synced with Laravel API")
            
    except Exception as e:
        logger.error(f"Error syncing user {user.id} with API: {e}")