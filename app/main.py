from fastapi import FastAPI
from app.src.routes.auth import router as auth_router
from app.src.routes.contacts import router as contacts_router

app = FastAPI(
    title="Contacts API",
    description="API for managing contacts",
    version="1.0.0",
    swagger_ui_parameters={
        "oauth2RedirectUrl": "/docs/oauth2-redirect",
        "persistAuthorization": True
    }
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(contacts_router, prefix="/contacts", tags=["contacts"])