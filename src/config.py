
import os
from pathlib import Path
from dotenv import load_dotenv

# Get project root (one level up from src)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# AI Provider Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Model Selection
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# Debugging: Print status (but mask the key)
if GROQ_API_KEY:
    masked_key = GROQ_API_KEY[:5] + "..." + GROQ_API_KEY[-4:] if len(GROQ_API_KEY) > 10 else "***"
    print(f"✅ GROQ_API_KEY loaded successfully: {masked_key}")
else:
    print("❌ FAILED to load GROQ_API_KEY from .env")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
    raise ValueError("GROQ_API_KEY is missing or invalid in .env file. Please add your real key.")
