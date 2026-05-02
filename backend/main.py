from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
import logging
import sys

# Add backend directory to path for imports
sys.path.insert(0, '/app/backend')

from routes.audio import router as audio_router
from db.mongo import shutdown_db

# Create FastAPI app
app = FastAPI(
    title="Audio Analysis API",
    description="Real-time audio pitch detection with PYIN algorithm",
    version="2.0.0"
)

# Include routers
app.include_router(audio_router, prefix="/api")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup_event():
    logger.info("Audio Analysis API v2.0 started")


@app.on_event("shutdown")
async def shutdown_event():
    await shutdown_db()
    logger.info("Audio Analysis API shutdown")
