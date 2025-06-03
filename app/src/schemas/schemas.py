from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import date
from typing import Optional 
class ContactBase(BaseModel): 
    first_name: str 
    last_name: str
    email: EmailStr
    phone_number: str  
    birthday: date
    additional_info: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)  
class ContactCreate(ContactBase):
    pass
class ContactUpdate(BaseModel):
    first_name: Optional[str] = None 
    last_name: Optional[str] = None 
    email: Optional[EmailStr] = None 
    phone_number: Optional[str] = None   
    additional_info: Optional[str] = None 
class ContactResponse(ContactBase): 
    id: int 