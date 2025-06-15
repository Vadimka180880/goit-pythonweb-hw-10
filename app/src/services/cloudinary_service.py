import cloudinary
import cloudinary.uploader
import cloudinary.api
from fastapi import UploadFile
from app.src.config.config import settings

cloudinary.config(
    cloud_name=settings.cloud_name,
    api_key=settings.cloud_api_key, 
    api_secret=settings.cloud_api_secret,   
    secure=True 
)
async def upload_avatar(file: UploadFile) -> str:
    result = cloudinary.uploader.upload(file.file, folder="avatars")
    return result["secure_url"]
