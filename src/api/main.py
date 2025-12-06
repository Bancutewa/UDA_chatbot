"""
FastAPI Main Application Entry Point
Real Estate AI Chatbot Backend
"""
import logging
import sys
import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from .routers import chat, listings, admin, schedule, data_management, auth, nlu_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        # logging.FileHandler("app.log") # Optional: log to file
    ]
)
logger = logging.getLogger("main")

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Real Estate AI Chatbot Backend")
    yield
    # Shutdown
    logger.info("Shutting down Real Estate AI Chatbot Backend")

# Create FastAPI app
app = FastAPI(
    title="Real Estate AI Chatbot API",
    description="Backend API for Vietnamese Real Estate AI Chatbot",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(listings.router, prefix="/listings", tags=["Listings"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(schedule.router, prefix="/schedule", tags=["Schedule"])
app.include_router(data_management.router, prefix="/data", tags=["Data Management"])
app.include_router(nlu_router.router, prefix="/nlu", tags=["NLU"])

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "real-estate-ai-chatbot"}


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Real Estate AI Chatbot Backend API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
