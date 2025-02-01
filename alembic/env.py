from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from alembic import context
from os import getenv
from dotenv import load_dotenv

# Импорты моделей и баз
from db.base import Base
from db.models import *

load_dotenv()

# Alembic Config object
config = context.config

# Настройка логгирования
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Указываем метаданные для автогенерации
target_metadata = Base.metadata
config.set_main_option("sqlalchemy.url", getenv('DB_URL'))

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url"),  # Используем async URL для асинхронного движка
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # Установка конфигурации контекста с асинхронной поддержкой
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()  # Закрытие движка после миграций

def do_run_migrations(connection):
    """Выполнение миграций в синхронном контексте."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata
    )

    with context.begin_transaction():
        context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    import asyncio
    asyncio.run(run_migrations_online())
