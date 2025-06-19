from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.src.database import get_db
from app.src.repository import contacts as repository_contacts
from app.src.schemas import ContactCreate, ContactUpdate, ContactResponse
from app.src.services.auth import get_current_user
from app.src.database.models import User, Contact
from datetime import date, timedelta
from typing import List     

router = APIRouter(tags=["contacts"])

@router.post("/", response_model=ContactResponse, status_code=201)
async def create_contact(       
    contact: ContactCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
): 
    """ 
    Create a new contact for the authenticated user
    """
    db_contact = await repository_contacts.create_contact(db, contact, current_user.id)
    return db_contact

@router.get("/", response_model=List[ContactResponse])
async def read_contacts(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of contacts for the authenticated user
    """
    contacts = await repository_contacts.get_contacts(db, current_user.id, skip=skip, limit=limit)
    return contacts

@router.get("/{contact_id}", response_model=ContactResponse)
async def read_contact(  
    contact_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a single contact by ID 
    """
    contact = await repository_contacts.get_contact(db, contact_id, current_user.id)
    if contact is None: 
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact  

@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    contact: ContactUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):  
    """
    Update a contact
    """
    db_contact = await repository_contacts.update_contact(db, contact_id, contact, current_user.id)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@router.delete("/{contact_id}", response_model=ContactResponse)
async def delete_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a contact
    """
    db_contact = await repository_contacts.delete_contact(db, contact_id, current_user.id)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@router.get("/search/", response_model=List[ContactResponse])
async def search_contacts(
    query: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search contacts by name or email
    """
    contacts = await repository_contacts.search_contacts(db, query, current_user.id)
    return contacts

@router.get("/upcoming_birthdays/", response_model=List[ContactResponse])
async def get_upcoming_birthdays(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get contacts with birthdays in the next 7 days
    """
    contacts = await repository_contacts.upcoming_birthdays(db, current_user.id)
    return contacts