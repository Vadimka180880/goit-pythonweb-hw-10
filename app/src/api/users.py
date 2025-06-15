from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.src.services.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    oauth2_scheme,
)
from app.src.databases.database import get_db
from app.src.models.models import User
from app.src.schemas.users import UserResponse, UserCreate, Token
from app.src.config.config import settings
from fastapi_limiter.depends import RateLimiter
from fastapi import File, UploadFile
from app.src.services.cloudinary_service import upload_avatar

router = APIRouter() 

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    credentials_exception = HTTPException(  
        status_code=status.HTTP_401_UNAUTHORIZED,   
        detail="Could not validate credentials", 
        headers={"WWW-Authenticate": "Bearer"},     
    )
    try:    
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")     
        if email is None:
            raise credentials_exception     
    except JWTError:
        raise credentials_exception         

    result = await db.execute(select(User).filter_by(email=email))
    user = result.scalar_one_or_none()  
    if user is None:
        raise credentials_exception
    return user     

@router.post("/signup", response_model=UserResponse, status_code=201) 
async def register_user(new_user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter_by(email=new_user.email))
    existing_user = result.scalar_one_or_none() 
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")

    hashed_password = get_password_hash(new_user.password) 
    user = User(email=new_user.email, password=hashed_password)
    db.add(user)
    await db.commit() 
    await db.refresh(user)
    return user

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter_by(email=form_data.username))
    user = result.scalar_one_or_none()  
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")  

    access_token = create_access_token(data={"sub": user.email}, expires_delta=settings.access_token_expire_minutes)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get(
    "/me",
    response_model=UserResponse,
    dependencies=[Depends(RateLimiter(times=1, seconds=60))]  # 👈 1 запит за 60 секунд
)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/verify", response_model=UserResponse)
async def verify_user(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.confirmed:
        return current_user

    current_user.confirmed = True
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user

@router.patch("/avatar", response_model=UserResponse)
async def update_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    avatar_url = await upload_avatar(file)
    current_user.avatar = avatar_url
    await db.commit()
    await db.refresh(current_user)
    return current_user
