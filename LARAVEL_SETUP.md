# Простая интеграция с Laravel

## Настройка в Laravel

### 1. Добавьте в .env Laravel только токен:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### 2. Создайте маршрут в routes/api.php:

```php
Route::get('/bot/token', function () {
    return response()->json([
        'token' => env('TELEGRAM_BOT_TOKEN')
    ]);
});
```

### 3. Запустите бота:

```bash
python bot.py
```

## Как это работает

1. Бот запускается и обращается к `http://localhost:8000/api/bot/token`
2. Laravel возвращает токен из .env
3. Бот получает токен и работает дальше через существующий API клиент

Всё остальное (БД, Zelle, админы) остается как есть в коде бота.