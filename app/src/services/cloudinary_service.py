import cloudinary
import cloudinary.uploader
from fastapi import UploadFile, HTTPException
from app.src.config.config import settings
from typing import Optional
import logging

# Налаштування логування
logger = logging.getLogger(__name__)

# Конфігурація Cloudinary
cloudinary.config(
    cloud_name=settings.cloud_name,
    api_key=settings.cloud_api_key,
    api_secret=settings.cloud_api_secret,
    secure=True
)

async def upload_avatar(file: UploadFile, user_email: str) -> Optional[str]:
    """
    Завантажує аватар на Cloudinary у папку 'avatars'.
    
    Args:
        file: Файл аватара (UploadFile)
        user_email: Email користувача для унікального імені файла
        
    Returns:
        URL завантаженого аватара або None у разі помилки
    """
    try:
        # Генеруємо унікальне ім'я файла на основі email
        public_id = f"avatars/{user_email.replace('@', '_')}"
        
        # Завантаження з обмеженням розміру та формату
        result = cloudinary.uploader.upload(
            file.file,
            public_id=public_id,
            folder="avatars",
            overwrite=True,
            resource_type="image",
            transformation=[
                {"width": 250, "height": 250, "crop": "fill"},
                {"quality": "auto"}
            ],
            allowed_formats=["jpg", "png", "jpeg"]
        )
        return result["secure_url"]
    
    except cloudinary.exceptions.Error as e:
        logger.error(f"Cloudinary upload error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload avatar: {str(e)}"
        )
    
    except Exception as e:
        logger.error(f"Unexpected upload error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Avatar upload failed"
        )