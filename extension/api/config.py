from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BROWSER_AGENT_PORT: int = 8000
    MAIN_API_URL: str = "http://host.docker.internal:8000"
    BROWSER_AGENT_API_KEY: str = ""
    CORS_ORIGINS: str = "*"

    class Config:
        env_file = ".env"

settings = Settings()
