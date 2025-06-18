from fastapi import FastAPI, HTTPException
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis
from fastapi.middleware.cors import CORSMiddleware
import smtplib
from app.src.routes.auth import router as auth_router
from app.src.routes.users import router as users_router
from app.src.config.config import settings

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(users_router, prefix="/users", tags=["users"])

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/test-smtp")
async def test_smtp():
    """Ручний тест SMTP (не обов'язковий)"""
    try:
        with smtplib.SMTP(settings.mail_server, settings.mail_port) as server:
            server.ehlo()
            if settings.mail_starttls:
                server.starttls()
                server.ehlo()
            server.login(settings.mail_username, settings.mail_password)
            return {"status": "SMTP connection successful"}
    except smtplib.SMTPAuthenticationError:
        raise HTTPException(
            status_code=500,
            detail="SMTP authentication failed. Check credentials in .env"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"SMTP error: {str(e)}"
        )

@app.on_event("startup")
async def startup():
    redis_connection = redis.Redis(host="localhost", port=6379, db=0)
    await FastAPILimiter.init(redis_connection)
    
    print("✅ Server started successfully")