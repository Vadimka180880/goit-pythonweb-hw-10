from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, or_, func
from app.src.database import models
from app.src.schemas import ContactCreate, ContactUpdate 
from datetime import date, timedelta 
    
async def create_contact(db: AsyncSession, contact: ContactCreate):
    new_contact = models.Contact(**contact.dict())
    db.add(new_contact) 
    await db.commit() 
    await db.refresh(new_contact)
    return new_contact  

async def get_contacts(db: AsyncSession):
    result = await db.execute(select(models.Contact))
    return result.scalars().all()

async def get_contact(db: AsyncSession, contact_id: int):
    result = await db.execute(select(models.Contact).where(models.Contact.id == contact_id))
    return result.scalar_one_or_none()

async def update_contact(db: AsyncSession, contact_id: int, contact_update: ContactUpdate):
    update_data = contact_update.dict(exclude_unset=True)
    if not update_data:
        return None
    await db.execute(
        update(models.Contact)
        .where(models.Contact.id == contact_id)
        .values(**update_data)
    )
    await db.commit()
    return await get_contact(db, contact_id)  
    
async def delete_contact(db: AsyncSession, contact_id: int):  
    contact = await get_contact(db, contact_id)
    if not contact: 
        return None   
    await db.execute(delete(models.Contact).where(models.Contact.id == contact_id))
    await db.commit()
    return contact   
    
async def search_contacts(db: AsyncSession, query: str):  
    result = await db.execute(
        select(models.Contact).where(  
            or_( 
                models.Contact.first_name.ilike(f"%{query}%"), 
                models.Contact.last_name.ilike(f"%{query}%"),
                models.Contact.email.ilike(f"%{query}%") 
            )
        )
    )
    return result.scalars().all()
    
async def upcoming_birthdays(db: AsyncSession):
    today = date.today()
    upcoming_date = today + timedelta(days=7)
    result = await db.execute(
        select(models.Contact).where(
            func.to_char(models.Contact.birthday, 'MM-DD').between(
                today.strftime('%m-%d'),
                upcoming_date.strftime('%m-%d')
            ) 
        ) 
    )
    return result.scalars().all() 
