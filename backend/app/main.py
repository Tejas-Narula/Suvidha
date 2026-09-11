from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import sessions, sarvam, health
from app.websocket import browser
from app.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Real-time Orchestration Backend for Voice Agent and Browser Extension",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For production, restrict this to chrome extension ID
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router, tags=["Health"])
app.include_router(sessions.router, prefix=f"{settings.API_V1_STR}/sessions", tags=["Sessions"])
app.include_router(sarvam.router, prefix=f"{settings.API_V1_STR}", tags=["Sarvam"])

# WebSocket Router
app.include_router(browser.router, prefix="/ws/browser", tags=["Browser WebSocket"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
