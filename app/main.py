from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware        
from app.src.api.endpoints import router as contacts_router
from app.src.api.users import router as users_router 

app = FastAPI()   

@app.get("/") 
async def root():
    return {"message": "Hello World"}  

@app.on_event("startup")
async def startup():
    redis_connection = redis.Redis(host="localhost", port=6379, db=0)
    await FastAPILimiter.init(redis_connection)
    
app.add_middleware( 
    CORSMiddleware, 
    allow_origins=["*"],    
    allow_credentials=True,
    allow_methods=["*"],        
    allow_headers=["*"],    
)
app.include_router(contacts_router, prefix="/contacts", tags=["contacts"])
app.include_router(users_router, prefix="/auth", tags=["auth"])   
