from pydantic_settings import BaseSettings
from pydantic import Field
class Settings(BaseSettings):
    database_url: str = Field(..., env="DATABASE_URL")  
    sync_database_url: str = Field(..., env="SYNC_DATABASE_URL")
    async_database_url: str = Field(..., env="ASYNC_DATABASE_URL")

    secret_key: str = "changeme"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    mail_username: str = ""
    mail_password: str = ""
    mail_from: str = "" 
    mail_port: int = 587
    mail_server: str = "smtp.example.com"   

    cloud_name: str = ""
    cloud_api_key: str = "" 
    cloud_api_secret: str = ""  

    class Config:
        env_file = ".env"   
        extra = "ignore"   

settings = Settings()
