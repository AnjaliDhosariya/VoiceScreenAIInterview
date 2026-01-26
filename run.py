# Run FastAPI Server
# Usage: python run.py

import uvicorn

if __name__ == "__main__":
    print("Starting VoiceScreen AI Server...")
    print("Server will be available at: http://localhost:8080")
    print("API documentation at: http://localhost:8080/docs")
    print("\nPress CTRL+C to stop the server\n")
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
