from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from routes.user import user_router
from routes.admin import admin_router
from services.admin import create_default_admin
from services.daily_reset import run_scheduler
import logging
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SOP Tracking System", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(user_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1/admin")

# Mount static files (frontend)
#app.mount("/", StaticFiles(directory="frontend", html=True), name="static")

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    try:
        await create_default_admin()
        # Start the scheduler in a separate thread
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True) # MODIFIED LINE
        scheduler_thread.start() # MODIFIED LINE
        logger.info("Application startup completed successfully - Daily reset scheduler started")
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "SOP Tracking System is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)