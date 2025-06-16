import asyncio
from datetime import datetime
from typing import Any, List, Dict
import logging

logger = logging.getLogger(__name__)


async def retry_async(func, max_retries: int = 3, delay: float = 1.0):
    """Повторяет выполнение асинхронной функции при ошибке"""
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            await asyncio.sleep(delay)


def format_price(price_kopecks: int) -> str:
    """Форматирует цену из копеек в рубли"""
    rubles = price_kopecks // 100
    kopecks = price_kopecks % 100
    
    if kopecks == 0:
        return f"{rubles} руб."
    else:
        return f"{rubles}.{kopecks:02d} руб."


def validate_phone(phone: str) -> bool:
    """Проверяет корректность номера телефона"""
    import re
    pattern = r'^(\+7|8)?[\s\-]?\(?[0-9]{3}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$'
    return bool(re.match(pattern, phone.replace(' ', '').replace('-', '')))


def truncate_text(text: str, max_length: int = 4096) -> str:
    """Обрезает текст до максимальной длины для Telegram"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def get_user_mention(user) -> str:
    """Создает упоминание пользователя"""
    if user.username:
        return f"@{user.username}"
    elif user.first_name and user.last_name:
        return f"{user.first_name} {user.last_name}"
    elif user.first_name:
        return user.first_name
    else:
        return f"User {user.id}"


async def send_notification(message: str, user_ids: List[int]):
    """Отправляет уведомление группе пользователей"""
    # Здесь можно реализовать отправку уведомлений
    # через API бота или другие каналы связи
    logger.info(f"Notification sent to {len(user_ids)} users: {message}")


def format_datetime(dt: datetime) -> str:
    """Форматирует дату и время для отображения"""
    return dt.strftime("%d.%m.%Y %H:%M")


def safe_int(value: Any, default: int = 0) -> int:
    """Безопасное преобразование в int"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default