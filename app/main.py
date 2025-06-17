from fastapi import FastAPI, Depends
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis
from fastapi.middleware.cors import CORSMiddleware
from app.src.api.endpoints import router as contacts_router
from app.src.api.users import router as users_router
from app.src.config.config import settings

app = FastAPI()     

@app.get("/")   
async def root():
    return {"message": "Hello World"}

@app.get("/test-smtp")
async def test_smtp():
    """Ендпоінт для тестування SMTP підключення"""
    import smtplib
    try:
        with smtplib.SMTP(settings.mail_server, settings.mail_port) as server:
            server.ehlo()
            if settings.mail_starttls:
                server.starttls()
            server.login(settings.mail_username, settings.mail_password)
            return {"status": "SMTP connection successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.on_event("startup")
async def startup():
    redis_connection = redis.Redis(host="localhost", port=6379, db=0)
    await FastAPILimiter.init(redis_connection)
    
    try:
        with smtplib.SMTP(settings.mail_server, settings.mail_port) as server:
            if settings.mail_starttls:
                server.starttls()
            server.login(settings.mail_username, settings.mail_password)
            print("SMTP connection test: SUCCESS")
    except Exception as e:
        print(f"SMTP connection test FAILED: {str(e)}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(contacts_router, prefix="/contacts", tags=["contacts"])
app.include_router(users_router, prefix="/auth", tags=["auth"])