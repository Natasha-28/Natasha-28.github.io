import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class TelegramService:
    def __init__(self):
        self.token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
        self.base_url = f"https://api.telegram.org/bot{self.token}"
    
    def send_message(self, chat_id, text, parse_mode='HTML'):
        """Отправка сообщения в Telegram"""
        if not self.token or not chat_id:
            logger.warning("Telegram токен или chat_id не настроены")
            return False
            
        url = f"{self.base_url}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка отправки сообщения в Telegram: {e}")
            return False
    
    def format_order_message(self, order):
        """Форматирование сообщения о заказе"""
        payment_method_map = {
            'online': '💳 Онлайн оплата',
            'courier': '📦 Оплата курьеру', 
            'card': '💳 Картой при получении',
            'cash': '💰 Наличными при получении'
        }
        
        status_map = {
            'pending': '⏳ Ожидает обработки',
            'processing': '🔄 В обработке',
            'shipped': '🚚 Отправлен',
            'delivered': '✅ Доставлен',
            'cancelled': '❌ Отменен'
        }
        
        message = f"""
🎉 <b>Новый заказ создан!</b>

📦 <b>Номер заказа:</b> {order.order_number}
👤 <b>Клиент:</b> {order.customer_name}
📞 <b>Телефон:</b> {order.customer_phone}
📧 <b>Email:</b> {order.customer_email}
📍 <b>Адрес:</b> {order.delivery_address}

💰 <b>Сумма:</b> {order.total_amount} руб.
💳 <b>Способ оплаты:</b> {payment_method_map.get(order.payment_method, order.payment_method)}
🔄 <b>Статус заказа:</b> {status_map.get(order.status, order.status)}

<i>Заказ ожидает обработки в админ-панели</i>
        """.strip()
        
        return message
    
    def send_order_notification(self, order):
        """Отправка уведомления о заказе"""
        if not order.telegram_chat_id:
            logger.warning(f"У заказа {order.id} не указан telegram_chat_id")
            return False
        
        message = self.format_order_message(order)
        return self.send_message(order.telegram_chat_id, message)