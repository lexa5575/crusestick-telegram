from aiogram import Router, types, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from keyboards.inline import get_main_menu
from states.order_states import OrderStates
from database.models import create_order, get_user_cart, clear_cart

router = Router()


@router.callback_query(F.data == "checkout")
async def start_checkout(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    cart_items = await get_user_cart(user_id)
    
    if not cart_items:
        await callback.answer("Корзина пуста!")
        return
    
    await callback.message.edit_text(
        "📍 Введите ваш адрес доставки:"
    )
    await state.set_state(OrderStates.waiting_for_address)


@router.message(OrderStates.waiting_for_address)
async def process_address(message: types.Message, state: FSMContext):
    address = message.text
    user_id = message.from_user.id
    
    # Создаем заказ
    order_id = await create_order(user_id, address)
    
    # Очищаем корзину
    await clear_cart(user_id)
    
    await message.answer(
        f"✅ Заказ #{order_id} успешно создан!\n\n"
        f"📍 Адрес доставки: {address}\n"
        f"📞 Мы свяжемся с вами для уточнения деталей.",
        reply_markup=get_main_menu()
    )
    
    await state.clear()