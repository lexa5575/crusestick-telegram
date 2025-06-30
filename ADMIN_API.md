# Admin HTTP API для отправки сообщений пользователям

## Обзор

Бот теперь запускает HTTP сервер на порту 8080 для получения команд от Laravel API.

## Доступные endpoints:

### 1. Отправка Zelle реквизитов пользователю

```http
POST http://localhost:8080/admin/zelle
Content-Type: application/json

{
  "telegram_id": 123456789,
  "message": "💵 <b>Реквизиты для оплаты вашего заказа!</b>\n\n📋 <b>Реквизиты для Zelle:</b>\n📧 Email: <code>merchant@example.com</code>\n\n📝 <b>В комментарии укажите:</b>\n<code>Order #12345</code>\n\n🕐 После оплаты мы обработаем ваш заказ.",
  "order_id": 12345
}
```

**Ответ:**
```json
{
  "success": true
}
```

### 2. Отправка трекинг номера пользователю

```http
POST http://localhost:8080/admin/tracking
Content-Type: application/json

{
  "telegram_id": 123456789,
  "message": "📦 <b>Ваш заказ #12345 отправлен!</b>\n\n📮 <b>Трекинг номер:</b> <code>9400136106193352646779</code>\n🚚 <b>Курьер:</b> USPS\n📅 <b>Ориентировочная дата доставки:</b> 25.06.2024\n\n🎉 Спасибо за покупку!",
  "tracking_number": "9400136106193352646779",
  "order_id": 12345
}
```

**Ответ:**
```json
{
  "success": true
}
```

## Ошибки

**400 Bad Request:**
```json
{
  "success": false,
  "error": "Missing required fields"
}
```

**500 Internal Server Error:**
```json
{
  "success": false,
  "error": "Error description"
}
```

## Примеры использования из Laravel

### Отправка Zelle реквизитов:

```php
$response = Http::post('http://localhost:8080/admin/zelle', [
    'telegram_id' => $user->telegram_id,
    'message' => "💵 <b>Реквизиты для оплаты заказа #{$order->id}!</b>\n\n📧 Email: <code>{$zelle_email}</code>\n\n📝 <b>В комментарии укажите:</b> <code>Order #{$order->id}</code>",
    'order_id' => $order->id
]);
```

### Отправка трекинга:

```php
$response = Http::post('http://localhost:8080/admin/tracking', [
    'telegram_id' => $user->telegram_id,
    'message' => "📦 <b>Заказ #{$order->id} отправлен!</b>\n\n📮 <b>Трекинг номер:</b> <code>{$order->tracking_number}</code>\n🚚 <b>Курьер:</b> USPS\n\n🎉 Спасибо за покупку!",
    'tracking_number' => $order->tracking_number,
    'order_id' => $order->id
]);
```

## Примечания

### USPS Tracking URL:
- Автоматически генерируется ссылка: `https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking_number}`
- Поддерживает все форматы USPS трекинг номеров
- Пример: `9400136106193352646779`

## Новые API endpoints для заказов

### 3. Получение заказов пользователя (для кнопки "Мои заказы")

Бот будет запрашивать заказы пользователя у Laravel:

```http
GET /api/bot/users/{telegram_user_id}/orders
```

**Ожидаемый ответ от Laravel:**
```json
{
  "data": [
    {
      "id": 12345,
      "status": "shipped",
      "total_amount": 299.99,
      "tracking_number": "9400136106193352646779",
      "created_at": "2024-06-21T10:30:00Z",
      "products": [
        {
          "name": "iPhone 15",
          "quantity": 1,
          "price": "299.99"
        }
      ],
      "shipping_address": {
        "first_name": "John",
        "last_name": "Doe",
        "street": "123 Main Street",
        "apartment": "Apt 5B",
        "city": "New York",
        "state": "NY",
        "zip_code": "10001",
        "phone": "+1234567890",
        "company": "Tech Corp"
      }
    }
  ]
}
```

**Если у пользователя нет заказов:**
```json
{
  "data": []
}
```