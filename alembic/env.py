from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from app.src.databases.models import Base
from dotenv import load_dotenv 
import os 

load_dotenv()

config = context.config 

if config.config_file_name is not None: 
    fileConfig(config.config_file_name) 

target_metadata = Base.metadata 

async_database_url = os.getenv("ASYNC_DATABASE_URL") 
if not async_database_url: 
    raise ValueError("ASYNC_DATABASE_URL is not set in .env")
config.set_main_option("sqlalchemy.url", async_database_url)    

def run_migrations_offline():   
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

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    ) 

    async def do_run_migrations(connection):
        await connection.run_sync(
            lambda sync_connection: context.configure(
                connection=sync_connection, 
                target_metadata=target_metadata,
            )
        ) 
        await connection.run_sync(context.run_migrations)

    import asyncio
    async def run(): 
        async with connectable.connect() as connection:
            await do_run_migrations(connection) 

    asyncio.run(run())  

if context.is_offline_mode():
    run_migrations_offline()
else:    
    run_migrations_online()
