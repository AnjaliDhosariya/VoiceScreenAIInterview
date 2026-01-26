# Run Streamlit Frontend
# Usage: python run_frontend.py

import subprocess
import sys

if __name__ == "__main__":
    print("=" * 60)
    print("Starting VoiceScreen AI - Streamlit Frontend")
    print("=" * 60)
    print("\n📋 Make sure the backend is running on http://localhost:8080")
    print("   (Run: python run.py in another terminal)\n")
    print("🌐 Frontend will open at: http://localhost:8501")
    print("\nPress CTRL+C to stop the frontend\n")
    print("=" * 60)
    print()
    
    import os
    app_path = os.path.join("src", "frontend", "frontend_app.py")
    subprocess.run([sys.executable, "-m", "streamlit", "run", app_path])
