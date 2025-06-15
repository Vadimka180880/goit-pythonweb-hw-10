from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session  

from app.src.schemas.users import UserCreate, UserResponse
from app.src.repository import users as repository_users
from app.src.databases.database import get_db   

router = APIRouter()

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)  
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = await repository_users.get_user_by_email(user.email, db)        
    if existing_user: 
        raise HTTPException(    
            status_code=status.HTTP_409_CONFLICT,    
            detail="User with this email already exists"    
        )
    return await repository_users.create_user(user, db) 