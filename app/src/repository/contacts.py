from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.src.database.models import Contact, User
from typing import Optional

async def get_contact(db: AsyncSession, contact_id: int, user: User) -> Optional[Contact]:
    result = await db.execute(
        select(Contact).filter_by(id=contact_id, user_id=user.id)
    )
    return result.scalars().first()