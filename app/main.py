from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
        
from app.src.api.endpoints import router as contacts_router
from app.src.api.users import router as users_router 

app = FastAPI()     

app.add_middleware( 
    CORSMiddleware, 
    allow_origins=["*"],    
    allow_credentials=True,
    allow_methods=["*"],        
    allow_headers=["*"],    
)

app.include_router(contacts_router, prefix="/contacts", tags=["contacts"])
app.include_router(users_router, prefix="/auth", tags=["auth"])   
