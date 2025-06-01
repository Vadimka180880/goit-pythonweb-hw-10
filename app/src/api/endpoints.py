from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.src.databases.database import get_db
from app.src.schemas.schemas import ContactCreate, ContactUpdate, ContactResponse
from app.src.crud.crud import get_contacts, get_contact, create_contact, update_contact, delete_contact

router = APIRouter()

@router.get("/contacts", response_model=list[ContactResponse])
async def read_contacts(db: AsyncSession = Depends(get_db)):
    return await get_contacts(db)   

@router.get("/contacts/{contact_id}", response_model=ContactResponse)
async def read_contact(contact_id: int, db: AsyncSession = Depends(get_db)):
    contact = await get_contact(db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@router.post("/contacts", response_model=ContactResponse)
async def create_new_contact(contact: ContactCreate, db: AsyncSession = Depends(get_db)):
    return await create_contact(db, contact)

@router.put("/contacts/{contact_id}", response_model=ContactResponse)
async def update_existing_contact(contact_id: int, contact: ContactUpdate, db: AsyncSession = Depends(get_db)):
    updated = await update_contact(db, contact_id, contact)
    if not updated:
        raise HTTPException(status_code=404, detail="Contact not found")
    return updated      

@router.delete("/contacts/{contact_id}")
async def delete_existing_contact(contact_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await delete_contact(db, contact_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"detail": "Contact deleted"}
