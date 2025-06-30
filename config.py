from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Telegram Bot Token (from environment variable)
    bot_token: str = Field(default="", env='TELEGRAM_BOT_TOKEN')
    
    # Laravel API URL
    laravel_api_url: str = Field('http://localhost:8000', env='LARAVEL_API_URL')
    
    # Debug mode
    debug: bool = Field(True, env='DEBUG')
    
    # Telegram API URL
    telegram_api_url: str = 'https://api.telegram.org'

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = 'ignore'


settings = Settings()

# Backward compatibility exports
BOT_TOKEN = settings.bot_token