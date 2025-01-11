import subprocess
import sys
from pathlib import Path

def setup_development():
    """Set up the development environment"""
    frontend_dir = Path("ai-assistant-frontend")
    
    # Check if frontend is built
    if not (frontend_dir / "build").exists():
        print("Building frontend...")
        try:
            subprocess.run(["npm", "run", "build"], check=True)
        except subprocess.CalledProcessError:
            print("Error building frontend. Please check npm and React installation.")
            sys.exit(1)
    
    # Start the development server
    print("Starting development server...")
    subprocess.run(["python", "-m", "uvicorn", "src.api:app", "--reload"])

if __name__ == "__main__":
    setup_development()
