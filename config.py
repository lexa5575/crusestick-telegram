from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List, Optional
import os
from dotenv import load_dotenv

# Принудительно загружаем .env файл если он есть
load_dotenv()
# Также пробуем загрузить из разных возможных путей на Render
load_dotenv('/opt/render/project/src/.env')
load_dotenv('./.env')


class Settings(BaseSettings):
    # Telegram Bot Token (from environment variable)
    bot_token: str = Field(default="", env='TELEGRAM_BOT_TOKEN')
    
    # Laravel API URL
    laravel_api_url: str = Field('https://crusestick.com', env='LARAVEL_API_URL')
    
    # Debug mode
    debug: bool = Field(True, env='DEBUG')
    
    # Admin IDs for notifications (comma-separated string)
    admin_ids_str: str = Field(default="", env='ADMIN_IDS')
    
    # Telegram API URL
    telegram_api_url: str = 'https://api.telegram.org'
    
    # Bot webhook URL for Laravel callbacks
    bot_webhook_url: str = Field(default="", env='BOT_WEBHOOK_URL')
    
    @property
    def admin_ids(self) -> List[int]:
        """Parse admin IDs from comma-separated string"""
        if not self.admin_ids_str.strip():
            return []
        try:
            return [int(x.strip()) for x in self.admin_ids_str.split(',') if x.strip()]
        except ValueError:
            return []
    
    # Optional webhook security settings
    webhook_secret: Optional[str] = Field(default=None, env='WEBHOOK_SECRET')
    allowed_webhook_origins: List[str] = Field(default_factory=list, env='ALLOWED_WEBHOOK_ORIGINS')

    @field_validator('admin_ids', mode='before')
    @classmethod
    def parse_admin_ids(cls, v):
        """Parse comma-separated admin IDs string into list of integers"""
        if isinstance(v, str):
            if not v.strip():
                return []
            try:
                return [int(x.strip()) for x in v.split(',') if x.strip()]
            except ValueError:
                return []
        elif isinstance(v, list):
            return v
        return []
    
    @field_validator('allowed_webhook_origins', mode='before')
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse comma-separated origins string into list"""
        if isinstance(v, str):
            if not v.strip():
                return []
            return [x.strip() for x in v.split(',') if x.strip()]
        elif isinstance(v, list):
            return v
        return []

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = 'ignore'


settings = Settings()

# Если pydantic не читает токен, берем его напрямую из переменных окружения
if not settings.bot_token and 'TELEGRAM_BOT_TOKEN' in os.environ:
    settings.bot_token = os.environ['TELEGRAM_BOT_TOKEN']

# Backward compatibility exports
BOT_TOKEN = settings.bot_token