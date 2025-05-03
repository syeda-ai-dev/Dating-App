from fastapi import APIRouter
from mhire.com.app.notification.notification import Notification
from mhire.com.config.config import Config

config = Config()
router = APIRouter(
    prefix="/notification",
    tags=["notification"],
    responses={404: {"description": "Not found"}},
)

notification_service = Notification(config)

@router.get("/generate")
async def generate_now():
    """Generate a new dating suggestion quote"""
    return await notification_service.store_daily_quote()
