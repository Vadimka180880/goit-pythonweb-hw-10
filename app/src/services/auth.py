from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.src.config.config import settings
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, status

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:     
    return pwd_context.verify(plain_password, hashed_password)  

def get_password_hash(password: str) -> str: 
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[int] = None):
    to_encode = data.copy()     
    expire = datetime.utcnow() + timedelta(     
        minutes=expires_delta if expires_delta else 15
    )
    to_encode.update({"exp": expire})   
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm) 
    return encoded_jwt
    
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token.credentials, settings.secret_key, algorithms=[settings.algorithm])  
        return payload
    except JWTError:
        raise credentials_exception
    
def decode_token(token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])  
    except JWTError:
        raise credentials_exception