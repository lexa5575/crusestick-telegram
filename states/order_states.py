from aiogram.fsm.state import State, StatesGroup

class OrderStates(StatesGroup):
    # Состояния корзины
    viewing_cart = State()
    editing_quantity = State()
    
    # Состояния оформления заказа
    entering_first_name = State()
    entering_last_name = State()
    entering_street = State()
    entering_city = State()
    entering_state = State()
    entering_zip_code = State()
    entering_phone = State()  # необязательное
    entering_apartment = State()  # необязательное
    entering_company = State()  # необязательное
    selecting_payment = State()
    entering_promocode = State()
    confirming_order = State()
    
    # Состояния для Zelle
    waiting_payment_proof = State()
    
    # Состояния промокода
    entering_promocode_code = State()

class CartStates(StatesGroup):
    viewing = State()
    editing_quantity = State()

class SupportStates(StatesGroup):
    """Состояния для системы поддержки"""
    entering_subject = State()  # Ввод темы обращения
    entering_message = State()  # Ввод сообщения