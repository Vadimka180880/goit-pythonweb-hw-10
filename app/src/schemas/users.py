from pydantic import BaseModel, EmailStr
class UserCreate(BaseModel):
    email: EmailStr 
    password: str   
class UserResponse(BaseModel): 
    id: int
    email: EmailStr
    confirmed: bool = False
    avatar: str | None = None
    class Config:
        from_attributes = True      
class Token(BaseModel):
    access_token: str
    token_type: str
