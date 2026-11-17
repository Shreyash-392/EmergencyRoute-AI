#!/usr/bin/env python3
"""
EmergencyRoute AI - Production Runner
Builds production frontend (if needed) and launches FastAPI server.
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT_DIR / "frontend"
FRONTEND_DIST = FRONTEND_DIR / "dist"

def ensure_frontend_built():
    if not (FRONTEND_DIST / "index.html").exists():
        print("[*] Production frontend build not found. Building now...")
        npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
        try:
            subprocess.run([npm_cmd, "run", "build"], cwd=str(FRONTEND_DIR), check=True)
            print("[+] Frontend built successfully.")
        except Exception as e:
            print(f"[!] Warning: Could not automatically build frontend ({e}). Backend API will still serve.")
    else:
        print("[+] Verified production frontend bundle at frontend/dist.")

def main():
    ensure_frontend_built()
    
    # Load environment variables
    from dotenv import load_dotenv
    env_path = ROOT_DIR / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print("[+] Loaded environment from .env.")
    else:
        print("[*] No .env found. Running with default environment settings.")

    host = os.environ.get("API_HOST", "0.0.0.0")
    port = int(os.environ.get("API_PORT", 8000))

    print(f"\n=======================================================")
    print(f" EmergencyRoute AI - Production Server Running")
    print(f" URL: http://{host}:{port}")
    print(f" Docs: http://{host}:{port}/docs")
    print(f" Telemetry & API keys strictly secured on server side.")
    print(f"=======================================================\n")

    import uvicorn
    uvicorn.run("app.main:app", app_dir=str(ROOT_DIR / "backend"), host=host, port=port, log_level="info")

if __name__ == "__main__":
    main()
