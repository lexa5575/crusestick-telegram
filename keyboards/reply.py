from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_contact_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="📱 Share Contact", request_contact=True)]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_location_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="📍 Share Location", request_location=True)]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )