from fastapi import APIRouter, HTTPException
from mhire.com.app.date_mate.date_mate import DateMate
from mhire.com.config.config import Config

config = Config()
router = APIRouter(
    prefix="/date-mate",
    tags=["date-mate"],
    responses={404: {"description": "Not found"}},
)

date_mate_service = DateMate(config)

@router.post("/chat")
async def chat(request: date_mate_service.ChatRequest):
    try:
        response = await date_mate_service.app.router.routes[-1].endpoint(request)
        return response
    except DateMateError as e:
        raise HTTPException(status_code=500, detail=str(e))
