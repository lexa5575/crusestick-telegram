from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from .connection import Base, async_session


class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(50))
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    
    cart_items = relationship("CartItem", back_populates="user")
    orders = relationship("Order", back_populates="user")


class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    price = Column(Integer, nullable=False)  # Цена в копейках
    image_url = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    
    cart_items = relationship("CartItem", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")


class CartItem(Base):
    __tablename__ = 'cart_items'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    quantity = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")


class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    total_amount = Column(Integer, nullable=False)
    address = Column(Text)
    status = Column(String(50), default='pending')
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = 'order_items'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    quantity = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)
    
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


# Функции для работы с базой данных

async def get_or_create_user(telegram_id: int, username: str = None, first_name: str = None, last_name: str = None):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        
        return user


async def get_products():
    async with async_session() as session:
        result = await session.execute(select(Product).where(Product.is_active == True))
        return result.scalars().all()


async def get_product(product_id: int):
    async with async_session() as session:
        result = await session.execute(select(Product).where(Product.id == product_id))
        return result.scalar_one_or_none()


async def add_to_cart(telegram_id: int, product_id: int, quantity: int = 1):
    async with async_session() as session:
        user = await get_or_create_user(telegram_id)
        
        result = await session.execute(
            select(CartItem).where(
                CartItem.user_id == user.id,
                CartItem.product_id == product_id
            )
        )
        cart_item = result.scalar_one_or_none()
        
        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = CartItem(
                user_id=user.id,
                product_id=product_id,
                quantity=quantity
            )
            session.add(cart_item)
        
        await session.commit()


async def get_user_cart(telegram_id: int):
    async with async_session() as session:
        user = await get_or_create_user(telegram_id)
        
        result = await session.execute(
            select(CartItem)
            .options(selectinload(CartItem.product))
            .where(CartItem.user_id == user.id)
        )
        return result.scalars().all()


async def remove_from_cart(telegram_id: int, product_id: int):
    async with async_session() as session:
        user = await get_or_create_user(telegram_id)
        
        result = await session.execute(
            select(CartItem).where(
                CartItem.user_id == user.id,
                CartItem.product_id == product_id
            )
        )
        cart_item = result.scalar_one_or_none()
        
        if cart_item:
            await session.delete(cart_item)
            await session.commit()


async def create_order(telegram_id: int, address: str):
    async with async_session() as session:
        user = await get_or_create_user(telegram_id)
        cart_items = await get_user_cart(telegram_id)
        
        total_amount = sum(item.product.price * item.quantity for item in cart_items)
        
        order = Order(
            user_id=user.id,
            total_amount=total_amount,
            address=address
        )
        session.add(order)
        await session.flush()
        
        for cart_item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
            session.add(order_item)
        
        await session.commit()
        return order.id


async def clear_cart(telegram_id: int):
    async with async_session() as session:
        user = await get_or_create_user(telegram_id)
        
        result = await session.execute(
            select(CartItem).where(CartItem.user_id == user.id)
        )
        cart_items = result.scalars().all()
        
        for item in cart_items:
            await session.delete(item)
        
        await session.commit()