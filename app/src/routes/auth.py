from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession
import jwt
from jwt.exceptions import PyJWTError as JWTError
import logging
from app.src.schemas.users import UserResponse, UserCreate, UserEmailSchema, ResetPasswordSchema
from app.src.services.auth import (
    create_access_token,
    verify_password,
    get_password_hash,
    get_current_user,
    reset_user_password
)
from app.src.repository.users import get_user_by_email, update_user_avatar
from app.src.database.database import get_db
from app.src.services.email import send_verification_email, send_password_reset_email, create_password_reset_token
from app.src.services.cloudinary_service import upload_avatar 
from app.src.config.config import settings
from app.src.database.models import User

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)

def create_verification_token(email: str) -> str:
    """
    Генерує токен спеціально для верифікації email.
    Відрізняється від access_token тим, що має type="email_verification".
    """
    expires = datetime.utcnow() + timedelta(hours=24)
    payload = {
        "sub": email,
        "exp": expires,
        "type": "email_verification"  
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

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
            
        if not user.confirmed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not verified. Please check your email for verification link.",
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

    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/signup", response_model=UserResponse)
async def signup(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    try:
        existing_user = await get_user_by_email(user_data.email, db)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email {user_data.email} already registered"
            )

        hashed_password = get_password_hash(user_data.password)
        new_user = User(email=user_data.email, password=hashed_password, confirmed=False)
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        verification_token = create_verification_token(user_data.email)
        background_tasks.add_task(send_verification_email, user_data.email, verification_token)

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
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        avatar_url = await upload_avatar(file, current_user.email)
        updated_user = await update_user_avatar(current_user.id, avatar_url, db)
        return UserResponse.from_orm(updated_user)
    except HTTPException as e:
        raise
    except Exception as e:
        logger.error(f"Update avatar error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Помилка при оновленні аватара"
        )

@router.get(
    "/me",
    response_model=UserResponse,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))]  
)
async def get_current_user_profile(
    request: Request,  
    current_user: User = Depends(get_current_user)
):
    return current_user

@router.get("/verify-email")
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Підтвердження email через токен
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email = payload.get("sub")
        token_type = payload.get("type")

        if not email or token_type != "email_verification":
            raise HTTPException(status_code=400, detail="Invalid token type")

        user = await get_user_by_email(email, db)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.confirmed:
            return {"message": "Email already verified"}

        user.confirmed = True
        await db.commit()

        return {"message": "Email successfully verified"}

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Verification token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid token")

@router.post("/password-reset-request", status_code=200)
async def request_password_reset(
    user_email: UserEmailSchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    user = await get_user_by_email(user_email.email, db)
    if not user:
        return {"message": "If the email exists, password reset instructions have been sent"}

    reset_token = create_password_reset_token(user_email.email)
    background_tasks.add_task(
        send_password_reset_email,
        email=user_email.email,
        reset_token=reset_token
    )

    return {"message": "Password reset instructions have been sent to your email"}

@router.post("/reset-password", status_code=200)
async def reset_password(
    reset_data: ResetPasswordSchema,
    db: AsyncSession = Depends(get_db)
):
    user = await reset_user_password(reset_data.token, reset_data.new_password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )

    return {"message": "Password has been reset successfully"}

@router.get("/test-redis")
async def test_redis(redis=Depends(get_redis)):
    await redis.set("test_key", "Hello, Redis!")
    value = await redis.get("test_key")
    return {"message": value}