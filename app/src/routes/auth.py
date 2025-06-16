from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from app.src.services.auth import (
    create_access_token,
    verify_password,
    decode_token
)
from app.src.repository.users import get_user_by_email 

router = APIRouter(tags=["auth"])

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await get_user_by_email(form_data.username)  
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=30 
    )        
    return {"access_token": access_token, "token_type": "bearer"}