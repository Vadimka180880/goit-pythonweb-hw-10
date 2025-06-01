from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.src.databases.models import Contact
from app.src.schemas.schemas import ContactCreate, ContactUpdate

async def get_contacts(db: AsyncSession):
    result = await db.execute(select(Contact))
    return result.scalars().all()   

async def get_contact(db: AsyncSession, contact_id: int):
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    return result.scalar_one_or_none()  

async def create_contact(db: AsyncSession, contact: ContactCreate):
    db_contact = Contact(**contact.dict())
    db.add(db_contact)
    await db.commit()
    await db.refresh(db_contact)
    return db_contact   

async def update_contact(db: AsyncSession, contact_id: int, contact: ContactUpdate):
    db_contact = await get_contact(db, contact_id)
    if db_contact:
        for var, value in contact.dict(exclude_unset=True).items():
            setattr(db_contact, var, value)
        await db.commit()
        await db.refresh(db_contact)
    return db_contact       

async def delete_contact(db: AsyncSession, contact_id: int):
    db_contact = await get_contact(db, contact_id)
    if db_contact:
        await db.delete(db_contact)
        await db.commit()
    return db_contact        