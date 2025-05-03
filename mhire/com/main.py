from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from mhire.com.app.match_making.match_making_router import router as match_making_router
from mhire.com.app.date_mate.date_mate_router import router as date_mate_router
from mhire.com.app.notification.notification_router import router as notification_router
from mhire.com.config.config import Config
import logging

config = Config()
app = FastAPI(
    title="Date Mate Application",
    description="Combined API for Match Making, Dating Advisor, and Notifications",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(match_making_router)
app.include_router(date_mate_router)
app.include_router(notification_router)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger = config.get_logger(__name__)
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

#if __name__ == "__main__":
#    import uvicorn
#    uvicorn.run("mhire.com.main:app", host="0.0.0.0", port=8000, reload=True)
