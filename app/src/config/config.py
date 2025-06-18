from pydantic_settings import BaseSettings
from pydantic import Field, RedisDsn

class Settings(BaseSettings):
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    sync_database_url: str = Field(..., env="SYNC_DATABASE_URL")
    async_database_url: str = Field(..., env="ASYNC_DATABASE_URL")

    # JWT
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)

    # Email
    mail_username: str = Field(..., env="MAIL_USERNAME")
    mail_password: str = Field(..., env="MAIL_PASSWORD")
    mail_from: str = Field(..., env="MAIL_FROM")
    mail_port: int = Field(default=587)
    mail_server: str = Field(default="smtp.gmail.com")
    mail_starttls: bool = Field(default=True)
    mail_ssl_tls: bool = Field(default=False)
    frontend_url: str = Field(default="http://localhost:8000")  

    # Cloudinary
    cloud_name: str = Field(..., env="CLOUD_NAME")
    cloud_api_key: str = Field(..., env="CLOUD_API_KEY")
    cloud_api_secret: str = Field(..., env="CLOUD_API_SECRET")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()