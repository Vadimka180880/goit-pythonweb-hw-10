from pydantic_settings import BaseSettings

class Settings(BaseSettings):  
    database_url: str
    sync_database_url: str  
    secret_key: str      
    algorithm: str
    access_token_expire_minutes: int 
    
    CLOUD_NAME=your_cloud_name
    CLOUD_API_KEY=your_api_key
    CLOUD_API_SECRET=your_api_secret
    
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str

    class Config:       
        env_file = ".env"       

settings = Settings()        
