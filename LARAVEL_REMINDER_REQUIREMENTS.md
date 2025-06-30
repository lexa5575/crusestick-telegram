# Laravel Reminder System Requirements

## Overview
All reminder logic has been moved from the Telegram bot to Laravel. The bot now only:
1. Sends activity tracking events to Laravel API
2. Receives reminder messages via HTTP endpoint

## Required Laravel Implementation

### 1. Database Tables

Create these tables in Laravel:

```php
// Migration: create_user_activities_table.php
Schema::create('user_activities', function (Blueprint $table) {
    $table->id();
    $table->bigInteger('telegram_user_id');
    $table->string('activity_type', 50); // 'cart_added', 'checkout_started', 'order_created', 'order_completed'
    $table->json('activity_data')->nullable();
    $table->timestamps();
    
    $table->index(['telegram_user_id', 'activity_type']);
    $table->index('created_at');
});

// Migration: create_scheduled_reminders_table.php
Schema::create('scheduled_reminders', function (Blueprint $table) {
    $table->id();
    $table->bigInteger('telegram_user_id');
    $table->string('reminder_type', 50); // 'abandon_cart', 'unpaid_order'
    $table->timestamp('scheduled_time');
    $table->boolean('is_sent')->default(false);
    $table->timestamp('sent_at')->nullable();
    $table->json('reminder_data')->nullable();
    $table->timestamps();
    
    $table->index(['telegram_user_id', 'reminder_type', 'is_sent']);
    $table->index(['is_sent', 'scheduled_time']);
});
```

### 2. API Endpoints

#### POST /api/user-activity
Receives activity tracking from bot:

```php
// UserActivityController.php
public function store(Request $request)
{
    $validated = $request->validate([
        'telegram_user_id' => 'required|integer',
        'activity_type' => 'required|string|in:cart_added,checkout_started,order_created,order_completed',
        'activity_data' => 'sometimes|array'
    ]);
    
    // Create activity record
    UserActivity::create($validated);
    
    // Handle reminder logic based on activity type
    $this->handleActivityReminder($validated);
    
    return response()->json(['success' => true]);
}

private function handleActivityReminder($activity)
{
    $userId = $activity['telegram_user_id'];
    $type = $activity['activity_type'];
    
    switch ($type) {
        case 'cart_added':
            // Cancel existing cart reminders
            $this->cancelReminders($userId, 'abandon_cart');
            // Schedule new cart reminder for +4 hours
            $this->scheduleReminder($userId, 'abandon_cart', now()->addHours(4));
            break;
            
        case 'checkout_started':
            // Cancel cart reminders when user starts checkout
            $this->cancelReminders($userId, 'abandon_cart');
            break;
            
        case 'order_created':
            // Cancel cart reminders (if any)
            $this->cancelReminders($userId, 'abandon_cart');
            // Schedule unpaid order reminder for +4 hours
            $orderId = $activity['activity_data']['order_id'] ?? null;
            $this->scheduleReminder($userId, 'unpaid_order', now()->addHours(4), ['order_id' => $orderId]);
            break;
            
        case 'order_completed':
            // Cancel all reminders when order is completed (tracking sent)
            $this->cancelReminders($userId, 'unpaid_order');
            break;
    }
}
```

### 3. Reminder Scheduler (Cron Job)

Create a Laravel command that runs every 5 minutes:

```php
// app/Console/Commands/SendPendingReminders.php
class SendPendingReminders extends Command
{
    protected $signature = 'reminders:send';
    protected $description = 'Send pending reminder notifications';

    public function handle()
    {
        $pendingReminders = ScheduledReminder::where('is_sent', false)
            ->where('scheduled_time', '<=', now())
            ->get();

        foreach ($pendingReminders as $reminder) {
            try {
                $success = $this->sendReminder($reminder);
                
                if ($success) {
                    $reminder->update([
                        'is_sent' => true,
                        'sent_at' => now()
                    ]);
                }
            } catch (Exception $e) {
                Log::error("Failed to send reminder {$reminder->id}: " . $e->getMessage());
            }
        }
        
        $this->info("Processed {$pendingReminders->count()} pending reminders");
    }

    private function sendReminder($reminder)
    {
        $message = $this->formatReminderMessage($reminder);
        
        // Send HTTP request to bot
        $response = Http::post(config('bot.webhook_url') . '/admin/reminder', [
            'telegram_id' => $reminder->telegram_user_id,
            'message' => $message,
            'reminder_type' => $reminder->reminder_type
        ]);
        
        return $response->successful();
    }
}
```

### 4. Reminder Message Templates

```php
private function formatReminderMessage($reminder)
{
    switch ($reminder->reminder_type) {
        case 'abandon_cart':
            return $this->formatAbandonCartMessage($reminder);
        case 'unpaid_order':
            return $this->formatUnpaidOrderMessage($reminder);
    }
}

private function formatAbandonCartMessage($reminder)
{
    // Get user's current cart items
    $userId = $reminder->telegram_user_id;
    $cartItems = $this->getUserCartItems($userId);
    
    if (empty($cartItems)) {
        return null; // Skip if cart is empty
    }
    
    $message = "🛒 <b>You have items waiting in your cart!</b>\n\n";
    $message .= "Don't miss out on your selected products. ";
    $message .= "Complete your purchase now and get them delivered to your door.\n\n";
    $message .= "🎯 <b>Your cart contains:</b>\n";
    
    $total = 0;
    foreach ($cartItems as $item) {
        $message .= "• {$item['name']} x{$item['quantity']} - \${$item['total']}\n";
        $total += $item['total'];
    }
    
    $message .= "\n💰 <b>Total: \${$total}</b>\n\n";
    $message .= "⏰ Complete your order now before items run out of stock!";
    
    return $message;
}

private function formatUnpaidOrderMessage($reminder)
{
    $orderId = $reminder->reminder_data['order_id'] ?? 'N/A';
    
    $message = "💳 <b>Payment reminder for Order #{$orderId}</b>\n\n";
    $message .= "We noticed you haven't completed the payment for your recent order. ";
    $message .= "Your order is still reserved and waiting for payment.\n\n";
    $message .= "📋 <b>What's next?</b>\n";
    $message .= "• Complete your payment to secure your items\n";
    $message .= "• Your order will be processed immediately after payment\n";
    $message .= "• Get tracking information once shipped\n\n";
    $message .= "⚠️ <b>Important:</b> Unpaid orders may be cancelled after 24 hours.\n\n";
    $message .= "💰 Complete your payment now to avoid losing your order!";
    
    return $message;
}
```

### 5. Cron Job Setup

Add to `app/Console/Kernel.php`:

```php
protected function schedule(Schedule $schedule)
{
    $schedule->command('reminders:send')
             ->everyFiveMinutes()
             ->withoutOverlapping();
}
```

### 6. Configuration

Add to `.env`:

```env
# Bot webhook URL for sending reminders
BOT_WEBHOOK_URL=http://localhost:8080
REMINDER_DELAY_HOURS=4
```

## Bot Endpoints (Already Implemented)

### POST http://localhost:8080/admin/reminder
Receives reminder requests from Laravel:

```json
{
    "telegram_id": 123456789,
    "message": "HTML formatted reminder message",
    "reminder_type": "abandon_cart" // or "unpaid_order"
}
```

## Activity Tracking Events

The bot sends these events to Laravel:

1. **cart_added** - When user adds product to cart
   ```json
   {
       "telegram_user_id": 123456789,
       "activity_type": "cart_added",
       "activity_data": {
           "product_id": 42,
           "product_name": "iPhone 15"
       }
   }
   ```

2. **checkout_started** - When user begins checkout process
   ```json
   {
       "telegram_user_id": 123456789,
       "activity_type": "checkout_started",
       "activity_data": {}
   }
   ```

3. **order_created** - When user confirms order
   ```json
   {
       "telegram_user_id": 123456789,
       "activity_type": "order_created",
       "activity_data": {
           "order_id": 12345,
           "payment_method": "zelle",
           "total_amount": 299.99
       }
   }
   ```

4. **order_completed** - When admin sends tracking number
   ```json
   {
       "telegram_user_id": 123456789,
       "activity_type": "order_completed",
       "activity_data": {
           "order_id": 12345
       }
   }
   ```

## Testing

1. **Test activity tracking:**
   - Add item to cart → Check Laravel receives `cart_added` event
   - Start checkout → Check Laravel receives `checkout_started` event
   - Create order → Check Laravel receives `order_created` event
   - Send tracking → Check Laravel receives `order_completed` event

2. **Test reminder scheduling:**
   - Verify reminders are scheduled 4 hours after activities
   - Check cron job processes pending reminders
   - Confirm bot receives and sends reminder messages

3. **Test reminder cancellation:**
   - Cart reminders cancelled when checkout starts
   - Order reminders cancelled when tracking is sent