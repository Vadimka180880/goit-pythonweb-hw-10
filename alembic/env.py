import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

from app.src.config.config import settings

from app.src import databases 
from app.src.databases.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.async_database_url)

target_metadata = Base.metadata

def run_migrations_offline():
    url = settings.async_database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},    
    )
    with context.begin_transaction():   
        context.run_migrations()

async def run_migrations_online():
    connectable = create_async_engine(
        settings.async_database_url,    
        poolclass=pool.NullPool
    )

    async with connectable.connect() as connection:
        await connection.run_sync(
            lambda conn: context.configure(         
                connection=conn,
                target_metadata=target_metadata,
                compare_type=True
            )
        )
        await connection.run_sync(lambda _: context.run_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
