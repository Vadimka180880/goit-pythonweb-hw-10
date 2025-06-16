from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.src.config.config import settings  
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:     
    return pwd_context.verify(plain_password, hashed_password)  

def get_password_hash(password: str) -> str: 
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[int] = None):
    to_encode = data.copy()     
    expire = datetime.utcnow() +  timedelta(     
        minutes=expires_delta if expires_delta else 15
    )
    to_encode.update({"exp": expire})   
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt
    