from pydantic import BaseModel, EmailStr
from datetime import date

class ContactBase(BaseModel):
    first_name: str
    last_name: str 
    email: EmailStr
    phone_number: str   
    birthday: date
    additional_info: str | None = None  
            
class ContactCreate(ContactBase):   
    pass
    
class ContactUpdate(BaseModel):
    first_name: str | None = None   
    last_name: str | None = None
    email: EmailStr | None = None
    phone_number: str | None = None  
    birthday: date | None = None
    additional_info: str | None = None
    
class ContactResponse(ContactBase): 
    id: int

    class Config:   
        from_attributes = True
