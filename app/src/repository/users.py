from app.src.databases.models import User
from app.src.schemas.users import UserCreate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext
from app.src.services.email import send_verification_email
from app.src.services.auth import create_access_token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def get_user_by_email(email: str, db: AsyncSession):
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()

async def create_user(user: UserCreate, db: AsyncSession):
    hashed_password = pwd_context.hash(user.password)
    db_user = User(email=user.email, password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    token = create_access_token(data={"sub": user.email})
    send_verification_email(user.email, token)

    return db_user

async def get_user_by_email(email: str):
        return await User.filter(email=email).first()