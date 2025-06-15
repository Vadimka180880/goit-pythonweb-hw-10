from pydantic import BaseModel, EmailStr    

class UserCreate(BaseModel):
    email: EmailStr 
    password: str

class UserResponse(BaseModel):    
    id: int     
    email: EmailStr     
    confirmed: bool         
    avatar: str | None = None    
    
    class Config:     
        orm_mode = True  
