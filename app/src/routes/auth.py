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
from app.src.repository.users import get_user_by_email, update_user_avatar, get_user_by_id
from app.src.services.email import send_verification_email, send_password_reset_email, create_password_reset_token
from app.src.services.cloudinary_service import upload_avatar 
from app.src.config.config import settings
from app.src.database.models import User
from app.src.database.redis import get_redis
from app.src.database.base import get_db

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)

@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new user account with the provided email and password. Sends a verification email to confirm the account."
)
async def signup(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    try:
        existing_user = await get_user_by_email(user_data.email, db)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email {user_data.email} already registered. Please use a different email or log in."
            )

        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            email=user_data.email,
            password=hashed_password,
            confirmed=False
        )   
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        background_tasks.add_task(
            send_verification_email,
            email=user_data.email,
            user_id=new_user.id
        )

        return UserResponse.from_orm(new_user)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user due to an internal server error."
        )

@router.post(
    "/login",
    response_model=dict,
    summary="Authenticate a user",
    description="Authenticates a user with email and password, returning JWT access token and user details."
)
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
                headers={"WWW-Authenticate": "Bearer"}
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
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get(
    "/verify-email",
    summary="Verify email",
    description="Verifies a user's email using the provided verification token sent to their email."
)
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        token_type = payload.get("type")

        if not user_id or token_type != "email_verification":
            logger.error(f"Invalid token payload: {payload}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type"
            )

        user = await get_user_by_id(int(user_id), db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if user.confirmed:
            return {"message": "Email already verified"}

        user.confirmed = True
        await db.commit()

        return {"message": "Email successfully verified"}

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token expired"
        )
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify email"
        )

@router.get(
    "/me",
    response_model=UserResponse,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
    summary="Get current user profile",
    description="Retrieves the profile information of the currently authenticated user."
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    return UserResponse.from_orm(current_user)

@router.patch(
    "/avatar",
    response_model=UserResponse,
    summary="Update user avatar",
    description="Uploads a new avatar for the authenticated user."
)
async def update_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        avatar_url = await upload_avatar(file, current_user.email)
        updated_user = await update_user_avatar(current_user.id, avatar_url, db)
        return UserResponse.from_orm(updated_user)
    except Exception as e:
        logger.error(f"Update avatar error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update avatar"
        )

@router.post(
    "/password-reset-request",
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
    description="Sends a password reset email."
)
async def request_password_reset(
    user_email: UserEmailSchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    try:
        user = await get_user_by_email(user_email.email, db)
        if not user:
            return {"message": "If the email exists, password reset instructions have been sent"}

        reset_token = create_password_reset_token(user_email.email)
        background_tasks.add_task(
            send_password_reset_email,
            email=user_email.email,
            reset_token=reset_token
        )

        return {"message": "Password reset instructions have been sent"}
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process password reset"
        )

@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Reset password",
    description="Resets the user's password."
)
async def reset_password(
    reset_data: ResetPasswordSchema,
    db: AsyncSession = Depends(get_db)
):
    try:
        if not reset_data.token or not reset_data.new_password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Token and new password are required"
            )

        user = await reset_user_password(reset_data.token, reset_data.new_password, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired token"
            )

        return {"message": "Password has been reset successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reset password error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )

@router.get(
    "/test-redis",
    summary="Test Redis connection"
)
async def test_redis(redis=Depends(get_redis)):
    try:
        await redis.set("test_key", "Hello, Redis!")
        value = await redis.get("test_key")
        return {"message": value.decode("utf-8") if value else "No value found"}
    except Exception as e:
        logger.error(f"Redis error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test Redis"
        )

@router.post(
    "/auth/login",
    response_model=dict,
    include_in_schema=False
)
async def swagger_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    return await login(form_data, db)