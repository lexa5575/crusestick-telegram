import aiohttp
import logging
from typing import List, Dict, Optional
from config import settings

logger = logging.getLogger(__name__)

class LaravelAPIClient:
    def __init__(self):
        self.base_url = settings.laravel_api_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Базовый метод для HTTP запросов"""
        url = f"{self.base_url}/api/bot{endpoint}"
        
        logger.debug(f"Making {method} request to {url}")
        
        try:
            async with self.session.request(method, url, **kwargs) as response:
                logger.debug(f"Response status: {response.status}")
                
                if response.status in [200, 201]:
                    result = await response.json()
                    logger.debug(f"Response data: {result}")
                    return result
                elif response.status == 404:
                    logger.warning(f"Resource not found: {url}")
                    return {}
                else:
                    error_text = await response.text()
                    logger.error(f"API request failed: {response.status} - {error_text}")
                    return {}
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected API request error: {e}")
            return {}
    
    async def get_products(self, category_id: Optional[int] = None, search: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
        """Получение списка товаров"""
        params = {}
        if category_id:
            params['category_id'] = category_id
        if search:
            params['search'] = search
        if limit:
            params['limit'] = limit
        else:
            # По умолчанию запрашиваем больше товаров или все
            params['limit'] = 1000  # Большой лимит для получения всех товаров
            
        response = await self._make_request('GET', '/products', params=params)
        return response.get('data', [])
    
    async def get_product(self, product_id: int) -> Optional[Dict]:
        """Получение одного товара по ID"""
        response = await self._make_request('GET', f'/products/{product_id}')
        return response.get('data') if response else None
    
    async def get_categories(self) -> List[Dict]:
        """Получение категорий"""
        response = await self._make_request('GET', '/categories')
        if isinstance(response, list):
            return response
        return response.get('data', [])
    
    async def create_or_update_user(self, user_data: Dict) -> Dict:
        """Создание или обновление пользователя"""
        return await self._make_request('POST', '/users', json=user_data)
    
    async def create_order(self, order_data: Dict) -> Dict:
        """Создание заказа"""
        return await self._make_request('POST', '/orders', json=order_data)
    
    
    async def check_promocode(self, code: str) -> Dict:
        """Проверка промокода"""
        return await self._make_request('GET', f'/promocodes/{code}')
    
    async def get_user_orders(self, telegram_user_id: int) -> Dict:
        """Получение заказов пользователя"""
        logger.info(f"Getting orders for user {telegram_user_id}")
        response = await self._make_request('GET', f'/users/{telegram_user_id}/orders')
        
        if not response:
            logger.warning(f"No orders found for user {telegram_user_id}")
            return {'orders': []}
        
        return response
    
    async def get_user_zelle(self, telegram_user_id: int) -> Dict:
        """Получение Zelle данных пользователя"""
        logger.info(f"Getting Zelle info for user {telegram_user_id}")
        response = await self._make_request('GET', f'/users/{telegram_user_id}/zelle')
        
        if not response:
            logger.warning(f"No Zelle data found for user {telegram_user_id}")
            return {
                'has_zelle': False,
                'zelle_email': None
            }
        
        # Laravel возвращает данные без обертки "data"
        return response
    
    async def track_user_activity(self, telegram_user_id: int, activity_type: str, activity_data: dict) -> Dict:
        """Отслеживание активности пользователя для системы напоминаний"""
        logger.info(f"Tracking activity {activity_type} for user {telegram_user_id}")
        
        data = {
            'telegram_user_id': telegram_user_id,
            'activity_type': activity_type,
            'activity_data': activity_data
        }
        
        response = await self._make_request('POST', '/user-activity', json=data)
        return response or {}

# Глобальный экземпляр клиента
api_client = LaravelAPIClient()