from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Вітаю! FastAPI працює чудово!"}