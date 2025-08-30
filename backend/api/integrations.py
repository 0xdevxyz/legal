"""Third-party integrations API"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/integrations", tags=["integrations"])

@router.get("/")
async def list_integrations():
    return {
        "integrations": ["Slack", "Jira", "Zapier", "Webhook"]
    }
