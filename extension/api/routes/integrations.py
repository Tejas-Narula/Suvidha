from fastapi import APIRouter
from api.models.intent import StartAutomationIntent
from api.routes.automations import start_automation

router = APIRouter()

@router.post("/start")
async def integrations_start(intent: StartAutomationIntent):
    # This is a transparent pass-through to /v1/automations as requested
    return await start_automation(intent)
