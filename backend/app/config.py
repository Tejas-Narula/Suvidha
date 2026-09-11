import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Government Service Orchestrator"
    API_V1_STR: str = "/api"
    
    # Supabase Vector DB config
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "https://vmozwacurzfxmolucnxc.supabase.co")
    SUPABASE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZtb3p3YWN1cnpmeG1vbHVjbnhjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4OTEyOTI5OSwiZXhwIjoyMTA0NzA1Mjk5fQ.FfrHT3W8f7FD8Iy_NC-vx-v4yWxLhKxO7DpYMix7B18"))
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZtb3p3YWN1cnpmeG1vbHVjbnhjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4OTEyOTI5OSwiZXhwIjoyMTA0NzA1Mjk5fQ.FfrHT3W8f7FD8Iy_NC-vx-v4yWxLhKxO7DpYMix7B18")
    
    # Sarvam / Auth
    API_KEY: str = "dev_secret_key"
    
    # Browser Agent API Config (Mock Variable / Endpoint)
    BROWSER_AGENT_API_URL: str = "http://localhost:8001/api/automate"
    BROWSER_AGENT_MOCK_MODE: bool = True

    # Session
    SESSION_EXPIRE_SECONDS: int = 3600

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
