from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    sync_database_url: str = Field(..., env="SYNC_DATABASE_URL")
    async_database_url: str = Field(..., env="ASYNC_DATABASE_URL")
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    # JWT Authentication
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    # Email SMTP
    mail_username: str
    mail_password: str
    mail_from: str
    mail_port: int
    mail_server: str
    mail_starttls: bool
    mail_ssl_tls: bool

    # Cloudinary
    cloud_name: str
    cloud_api_key: str
    cloud_api_secret: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()