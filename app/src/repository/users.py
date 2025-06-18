from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from passlib.context import CryptContext
from app.src.database.models import User  # Змінено з database на database
from app.src.schemas.users import UserCreate
from app.src.services.email import send_verification_email
from app.src.services.auth import create_access_token
from datetime import timedelta
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
async def get_user_by_email(email: str, db: AsyncSession) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()

async def create_user(user: UserCreate, db: AsyncSession) -> User:
    existing_user = await get_user_by_email(user.email, db)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    hashed_password = pwd_context.hash(user.password)
    db_user = User(email=user.email, password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    # Відправка email для підтвердження
    try:
        token = create_access_token(
            data={"sub": user.email},
            expires_delta=timedelta(hours=24)
        )
        await send_verification_email(user.email, token)
    except Exception as e:
        logger.error(f"Failed to send verification email: {e}")
        # Продовжуємо роботу навіть якщо email не відправлено

    return db_user  

async def update_user_avatar(user_id: int, avatar_url: str, db: AsyncSession) -> User:
    stmt = (
        update(User)
        .where(User.id == user_id)
        .values(avatar=avatar_url)
        .returning(User)
    )
    result = await db.execute(stmt)
    await db.commit()
    updated_user = result.scalars().first()
    
    if not updated_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    return updated_user