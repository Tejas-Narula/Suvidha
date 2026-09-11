from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Government Service Orchestrator"
    API_V1_STR: str = "/api"
    
    # Supabase Vector DB config
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    
    # Sarvam / Auth
    API_KEY: str = "dev_secret_key"
    
    # Session
    SESSION_EXPIRE_SECONDS: int = 3600

    class Config:
        env_file = ".env"

settings = Settings()
