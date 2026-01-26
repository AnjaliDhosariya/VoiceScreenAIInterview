import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables before ANY other internal imports
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# Now safe to import internal routes that depend on config
from src.routes.interview_routes import router as interview_router, ats_router
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="VoiceScreen AI - Interview Agent",
    description="Autonomous AI-led phone interview system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(interview_router)
app.include_router(ats_router)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "VoiceScreen AI",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy"}

if __name__ == "__main__":
    # Run with: python -m uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)
