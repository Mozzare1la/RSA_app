from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Настройки базы данных
    DATABASE_URL: str = "sqlite:///./users.db"
    
    # Настройки безопасности
    SECRET_KEY: str = "key12345"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings()