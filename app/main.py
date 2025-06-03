from fastapi import FastAPI
from app.src.api.endpoints import router as contacts_router     
    
app = FastAPI(title="Contacts CRUD API")     

app.include_router(contacts_router) 
