from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import settings

# Базовый класс для моделей
class Base(DeclarativeBase):
    pass

# Создаем движок БД
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=10,
    max_overflow=20
)

# Создаем фабрику сессий
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db():
    """Инициализация БД"""
    async with engine.begin() as conn:
        # Создаем таблицы если их нет (опционально)
        # await conn.run_sync(Base.metadata.create_all)
        pass

async def get_session() -> AsyncSession:
    """Получение сессии БД"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()