import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from config import settings
from keyboards.inline import help_keyboard, cancel_support_keyboard, back_to_menu_keyboard
from states.order_states import SupportStates
from services.admin_notifications import send_support_message

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data == "help")
async def show_help_menu(callback: CallbackQuery, state: FSMContext):
    """Показать меню помощи"""
    await state.clear()
    
    help_text = (
        "ℹ️ <b>Раздел помощи</b>\n\n"
        "📝 Если у вас возникли вопросы или проблемы, "
        "вы можете написать администратору.\n\n"
        "Мы постараемся ответить как можно быстрее!"
    )
    
    await callback.message.edit_text(
        help_text,
        reply_markup=help_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "contact_admin")
async def start_contact_admin(callback: CallbackQuery, state: FSMContext):
    """Начать процесс обращения к администратору"""
    await state.set_state(SupportStates.entering_subject)
    
    await callback.message.edit_text(
        "📝 <b>Обращение к администратору</b>\n\n"
        "📋 Сначала укажите тему вашего обращения:\n\n"
        "Например:\n"
        "• Вопрос по заказу\n"
        "• Проблема с оплатой\n"
        "• Предложение\n"
        "• Техническая проблема\n\n"
        "Введите тему:",
        reply_markup=cancel_support_keyboard()
    )
    await callback.answer()

@router.message(SupportStates.entering_subject)
async def process_support_subject(message: Message, state: FSMContext):
    """Обработка темы обращения"""
    subject = message.text.strip()
    
    if len(subject) < 3:
        await message.answer(
            "❌ Тема слишком короткая. Пожалуйста, опишите тему более подробно (минимум 3 символа)."
        )
        return
    
    if len(subject) > 100:
        await message.answer(
            "❌ Тема слишком длинная. Максимум 100 символов."
        )
        return
    
    await state.update_data(subject=subject)
    await state.set_state(SupportStates.entering_message)
    
    await message.answer(
        "✅ <b>Тема принята!</b>\n\n"
        f"📋 <b>Тема:</b> {subject}\n\n"
        "💬 Теперь опишите вашу проблему или вопрос подробнее:",
        reply_markup=cancel_support_keyboard()
    )

@router.message(SupportStates.entering_message)
async def process_support_message(message: Message, state: FSMContext):
    """Обработка сообщения пользователя"""
    user_message = message.text.strip()
    
    if len(user_message) < 10:
        await message.answer(
            "❌ Сообщение слишком короткое. Пожалуйста, опишите вашу проблему более подробно (минимум 10 символов)."
        )
        return
    
    if len(user_message) > 1000:
        await message.answer(
            "❌ Сообщение слишком длинное. Максимум 1000 символов."
        )
        return
    
    # Получаем данные из состояния
    data = await state.get_data()
    subject = data.get('subject', 'Без темы')
    
    # Данные пользователя
    user_data = {
        'telegram_id': message.from_user.id,
        'first_name': message.from_user.first_name,
        'last_name': message.from_user.last_name,
        'username': message.from_user.username
    }
    
    # Данные обращения
    support_data = {
        'subject': subject,
        'message': user_message
    }
    
    try:
        # Отправляем сообщение администратору
        await send_support_message(support_data, user_data, message.bot)
        
        await message.answer(
            "✅ <b>Ваше обращение отправлено!</b>\n\n"
            f"📋 <b>Тема:</b> {subject}\n"
            f"💬 <b>Сообщение:</b> {user_message}\n\n"
            "📱 Администратор получил ваше сообщение и свяжется с вами в ближайшее время.\n\n"
            "Спасибо за обращение!",
            reply_markup=back_to_menu_keyboard()
        )
        
        logger.info(f"Support message sent from user {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"Failed to send support message from user {message.from_user.id}: {e}")
        
        await message.answer(
            "❌ <b>Ошибка при отправке</b>\n\n"
            "Произошла ошибка при отправке вашего сообщения. "
            "Пожалуйста, попробуйте позже или обратитесь к администратору напрямую.",
            reply_markup=back_to_menu_keyboard()
        )
    
    await state.clear()

@router.callback_query(F.data == "cancel_support")
async def cancel_support(callback: CallbackQuery, state: FSMContext):
    """Отмена обращения в поддержку"""
    await state.clear()
    
    await callback.message.edit_text(
        "❌ <b>Обращение отменено</b>\n\n"
        "Если передумаете, вы всегда можете обратиться к нам через раздел помощи.",
        reply_markup=back_to_menu_keyboard()
    )
    await callback.answer("Request cancelled")