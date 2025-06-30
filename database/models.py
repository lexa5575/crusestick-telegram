from sqlalchemy import BigInteger, String, Boolean, DateTime, Text, JSON, Numeric, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timedelta
from .connection import Base

class TelegramUser(Base):
    __tablename__ = 'telegram_users'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    username: Mapped[str] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[str] = mapped_column(String(255), nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    preferences: Mapped[dict] = mapped_column(JSON, nullable=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    last_activity: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class TelegramOrder(Base):
    __tablename__ = 'telegram_orders'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_user_id: Mapped[int] = mapped_column(Integer)
    products: Mapped[dict] = mapped_column(JSON)
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2))
    discount_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2))
    promocode: Mapped[str] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default='pending')
    payment_method: Mapped[str] = mapped_column(String(50), nullable=True)
    tracking_number: Mapped[str] = mapped_column(String(255), nullable=True)
    customer_notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)