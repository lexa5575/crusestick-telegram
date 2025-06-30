from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
import aiohttp
import asyncio
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # Laravel API URL - можно задать через переменную окружения или изменить здесь
    laravel_api_url: str = Field('http://localhost:8000', env='LARAVEL_API_URL')
    
    # Динамически загружаемые настройки из Laravel
    bot_token: Optional[str] = None
    debug: bool = True
    telegram_api_url: str = 'https://api.telegram.org'
    
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = 'ignore'
    
    async def load_from_laravel(self):
        """Загрузка токена бота из Laravel API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.laravel_api_url}/api/bot/token") as response:
                    if response.status == 200:
                        config = await response.json()
                        
                        # Получаем только токен из Laravel
                        self.bot_token = config.get('token')
                        
                        if self.bot_token:
                            logger.info("Bot token loaded from Laravel successfully")
                            return True
                        else:
                            logger.error("No bot token in Laravel response")
                    else:
                        logger.warning(f"Laravel API returned status {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to load token from Laravel: {e}")
        
        logger.error("Could not get bot token from Laravel!")
        return False


settings = Settings()

# Backward compatibility exports
BOT_TOKEN = settings.bot_token