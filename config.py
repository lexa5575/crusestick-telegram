from pydantic_settings import BaseSettings
from pydantic import Field
import os
from dotenv import load_dotenv

# Принудительно загружаем .env файл если он есть
load_dotenv()
# Также пробуем загрузить из разных возможных путей на Render
load_dotenv('/opt/render/project/src/.env')
load_dotenv('./.env')

# Отладочная информация
print("DEBUG: Environment variables:")
print(f"TELEGRAM_BOT_TOKEN exists: {'TELEGRAM_BOT_TOKEN' in os.environ}")
print(f"TELEGRAM_BOT_TOKEN value length: {len(os.environ.get('TELEGRAM_BOT_TOKEN', ''))}")

class Settings(BaseSettings):
    # Telegram Bot Token (from environment variable)
    bot_token: str = Field(default="", env='TELEGRAM_BOT_TOKEN')
    
    # Laravel API URL
    laravel_api_url: str = Field('https://crusestick.com', env='LARAVEL_API_URL')
    
    # Debug mode
    debug: bool = Field(True, env='DEBUG')
    
    # Telegram API URL
    telegram_api_url: str = 'https://api.telegram.org'

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = 'ignore'


settings = Settings()

# Если pydantic не читает токен, берем его напрямую из переменных окружения
if not settings.bot_token and 'TELEGRAM_BOT_TOKEN' in os.environ:
    settings.bot_token = os.environ['TELEGRAM_BOT_TOKEN']
    print(f"DEBUG: Token loaded directly from os.environ, length: {len(settings.bot_token)}")

# Backward compatibility exports
BOT_TOKEN = settings.bot_token