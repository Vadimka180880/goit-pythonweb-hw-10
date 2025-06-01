from fastapi import FastAPI
from app.src.api import endpoints

app = FastAPI()
app.include_router(endpoints.router)

@app.get("/")
async def root():
    return {"message": "Вітаю! FastAPI працює чудово 2!"}  