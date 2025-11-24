from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
import random
import string

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название')
    slug = models.SlugField(unique=True, verbose_name='URL')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

class Product(models.Model):
    MATERIALS = (
        ('gold', 'Золото'),
        ('silver', 'Серебро'),
        ('platinum', 'Платина'),
    )

    name = models.CharField(max_length=200, verbose_name='Название')
    slug = models.SlugField(unique=True, verbose_name='URL')
    description = models.TextField(verbose_name='Описание')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категория')
    
    material = models.CharField(max_length=20, choices=MATERIALS, verbose_name='Материал')
    purity = models.PositiveIntegerField(verbose_name='Проба', help_text="Например, 585 для золота")
    weight = models.FloatField(verbose_name='Вес (г)', help_text="Вес в граммах")
    
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], verbose_name='Цена')
    in_stock = models.BooleanField(default=True, verbose_name='В наличии')
    
    main_image = models.ImageField(upload_to='products/', verbose_name='Главное изображение')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Ожидает обработки'),
        ('processing', 'В обработке'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    )
    
    PAYMENT_METHOD_CHOICES = (
    ('online', 'Онлайн оплата'),
    ('courier', 'Оплата курьеру'),
    ('card', 'Картой при получении'),
    ('cash', 'Наличными при получении'),
    )

    PAYMENT_STATUS_CHOICES = (
    ('pending', 'Ожидает оплаты'),
    ('paid', 'Оплачен'),
    ('failed', 'Ошибка оплаты'),
    )

    # Информация о заказе
    order_number = models.CharField(max_length=20, unique=True, verbose_name='Номер заказа')
    
    # Информация о клиенте
    customer_name = models.CharField(max_length=100, verbose_name='Имя клиента')
    customer_phone = models.CharField(max_length=20, verbose_name='Телефон')
    customer_email = models.EmailField(verbose_name='Email')
    delivery_address = models.TextField(verbose_name='Адрес доставки')
    
    # Telegram информация
    telegram_chat_id = models.BigIntegerField(null=True, blank=True, verbose_name='ID чата в Telegram')
    
    # Статусы
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус заказа')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending', verbose_name='Статус оплаты')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='courier', verbose_name='Способ оплаты')
        
    # Время доставки
    desired_delivery_date = models.DateField(null=True, blank=True, verbose_name='Желаемая дата доставки')
    desired_delivery_time = models.TimeField(null=True, blank=True, verbose_name='Желаемое время доставки')
    
    # Финансы
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Общая сумма')
    
    # Технические поля
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)
    
    def generate_order_number(self):
        return f"JL{self.created_at.strftime('%y%m%d')}{''.join(random.choices(string.digits, k=6))}"
    
    def __str__(self):
        return f"Заказ {self.order_number}"

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='Заказ')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    class Meta:
        verbose_name = 'Элемент заказа'
        verbose_name_plural = 'Элементы заказа'
class Cart(models.Model):
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def total_price(self):
        return self.product.price * self.quantity
class Cart(models.Model):
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def total_price(self):
        return self.product.price * self.quantity