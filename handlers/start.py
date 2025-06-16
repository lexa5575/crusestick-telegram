from aiogram import Router, types
from aiogram.filters import CommandStart
from keyboards.inline import get_main_menu

router = Router()


@router.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer(
        "👋 Добро пожаловать в наш магазин!\n\n"
        "Выберите действие:",
        reply_markup=get_main_menu()
    )