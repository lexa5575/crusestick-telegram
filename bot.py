import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import settings
from handlers import start, catalog, cart, orders, support
from handlers.admin_webhook import create_admin_app
from services.api_client import api_client

# Logging configuration
logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def start_admin_server():
    """Start HTTP server for admin commands"""
    app = create_admin_app()
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Start on port 8081 (bind to all interfaces for Render)
    site = web.TCPSite(runner, '0.0.0.0', 8081)
    await site.start()
    logger.info("Admin HTTP server started on http://0.0.0.0:8081")
    return runner

async def main():
    """Main bot startup function"""
    
    logger.info("Starting bot with token from environment...")
    
    # Проверяем токен
    if not settings.bot_token or len(settings.bot_token) < 10:
        logger.error(f"Invalid bot token! Length: {len(settings.bot_token) if settings.bot_token else 0}")
        logger.error(f"Token starts with: {settings.bot_token[:10] if settings.bot_token else 'None'}...")
        return
    
    logger.info(f"Bot token loaded successfully. Length: {len(settings.bot_token)}")
    
    # Bot initialization
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Dispatcher initialization
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Router registration
    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(cart.router)
    dp.include_router(orders.router)
    dp.include_router(support.router)
    
    # Start HTTP server for admin commands
    admin_runner = await start_admin_server()
    
    logger.info("Bot starting in polling mode...")
    
    try:
        # Start polling
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await admin_runner.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")