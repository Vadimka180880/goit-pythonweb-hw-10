from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.src.schemas.users import UserResponse, UserCreate
from app.src.services.auth import (
    create_access_token,
    verify_password,
    get_password_hash,
    get_current_user
)
from app.src.repository.users import get_user_by_email, update_user_avatar
from app.src.database.database import get_db
from app.src.services.email import send_verification_email
from app.src.services.cloudinary_service import upload_avatar 
from app.src.config.config import settings
from app.src.database.models import User 
import logging

router = APIRouter(tags=["auth"])
logger = logging.getLogger(__name__)

@router.post("/login", response_model=dict)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    try:
        user = await get_user_by_email(form_data.username, db)
        if not user or not verify_password(form_data.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse.from_orm(user)
        }
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/signup", response_model=UserResponse)
async def signup(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        existing_user = await get_user_by_email(user_data.email, db)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email {user_data.email} already registered"
            )

        hashed_password = get_password_hash(user_data.password)
        new_user = User(email=user_data.email, password=hashed_password)
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        try:
            verification_token = create_access_token(
                data={"sub": user_data.email},
                expires_delta=timedelta(hours=24)
            )
            await send_verification_email(user_data.email, verification_token)
        except Exception as e:
            logger.error(f"Failed to send verification email: {str(e)}")
            # Продовжуємо роботу навіть якщо email не відправлено

        return UserResponse.from_orm(new_user)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.patch("/avatar", response_model=UserResponse)
async def update_avatar(
    file: UploadFile = File(..., max_length=5_000_000),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only images are allowed"
        )

    try:
        avatar_url = await upload_avatar(file, current_user.email)
        updated_user = await update_user_avatar(current_user.id, avatar_url, db)
        return UserResponse.from_orm(updated_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Avatar upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )