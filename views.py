from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Product, Category, Order, OrderItem, Cart, CartItem
from telegram_bot.services import TelegramService
import uuid

def get_or_create_cart(request):
    """Получаем или создаем корзину"""
    if not request.session.session_key:
        request.session.create()
    
    cart, created = Cart.objects.get_or_create(session_key=request.session.session_key)
    return cart

def home(request):
    """Главная страница"""
    products = Product.objects.filter(in_stock=True)[:8]
    return render(request, 'store/home.html', {'products': products})

def product_list(request):
    """Список всех товаров"""
    category_slug = request.GET.get('category')
    products = Product.objects.filter(in_stock=True)
    
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    categories = Category.objects.all()
    return render(request, 'store/product_list.html', {
        'products': products,
        'categories': categories,
        'current_category': category_slug
    })

def product_detail(request, slug):
    """Детальная страница товара"""
    product = get_object_or_404(Product, slug=slug)
    return render(request, 'store/product_detail.html', {'product': product})

def add_to_cart(request, product_id):
    """Добавление товара в корзину"""
    product = get_object_or_404(Product, id=product_id)
    cart = get_or_create_cart(request)
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    return JsonResponse({'success': True, 'message': 'Товар добавлен в корзину'})

def cart_view(request):
    """Просмотр корзины"""
    cart = get_or_create_cart(request)
    return render(request, 'store/cart.html', {'cart': cart})

def update_cart(request, item_id):
    """Обновление количества товара в корзине"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__session_key=request.session.session_key)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'increase':
            cart_item.quantity += 1
        elif action == 'decrease' and cart_item.quantity > 1:
            cart_item.quantity -= 1
        elif action == 'remove':
            cart_item.delete()
            return JsonResponse({'success': True})
        
        cart_item.save()
        return JsonResponse({'success': True, 'quantity': cart_item.quantity})

def create_order(request):
    """Создание заказа"""
    if request.method == 'POST':
        try:
            # Получаем данные из формы
            customer_name = request.POST.get('customer_name')
            customer_phone = request.POST.get('customer_phone')
            customer_email = request.POST.get('customer_email')
            delivery_address = request.POST.get('delivery_address')
            telegram_chat_id = request.POST.get('telegram_chat_id')
            payment_method = request.POST.get('payment_method', 'courier')
            
            # Получаем корзину и рассчитываем сумму
            cart = get_or_create_cart(request)
            total_amount = sum(item.total_price() for item in cart.items.all())
            
            if total_amount == 0:
                return JsonResponse({
                    'success': False,
                    'message': 'Корзина пуста'
                })
            
            # Генерируем номер заказа
            import random
            import string
            from datetime import datetime
            
            order_number = f"JL{datetime.now().strftime('%y%m%d')}{''.join(random.choices(string.digits, k=6))}"
            
            # Создаем заказ
            order = Order.objects.create(
                order_number=order_number,
                customer_name=customer_name,
                customer_phone=customer_phone,
                customer_email=customer_email,
                delivery_address=delivery_address,
                telegram_chat_id=telegram_chat_id if telegram_chat_id else None,
                total_amount=total_amount,
                payment_method=payment_method,
                payment_status='paid' if payment_method == 'online' else 'pending'
            )
            
            # Переносим товары из корзины в заказ
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price
                )
            
            # Очищаем корзину
            cart.items.all().delete()
            
            # ОТПРАВЛЯЕМ УВЕДОМЛЕНИЕ В TELEGRAM
            if order.telegram_chat_id:
                telegram_service = TelegramService()
                telegram_service.send_order_notification(order)
            
            return JsonResponse({
                'success': True,
                'order_number': order.order_number,
                'message': f'Заказ {order.order_number} успешно создан! Способ оплаты: {order.get_payment_method_display()}. Скоро с вами свяжутся для подтверждения.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Ошибка при создании заказа: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Неверный метод запроса'})