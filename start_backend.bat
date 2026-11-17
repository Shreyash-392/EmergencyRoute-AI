@echo off
title EmergencyRoute AI - FastAPI Backend (Port 8000)
cd /d "%~dp0"
echo Starting FastAPI Backend on http://127.0.0.1:8000 ...
set "PY_EXE=C:\Users\Shreyash\AppData\Local\Programs\Python\Python310\python.exe"
if not exist "%PY_EXE%" set "PY_EXE=python"
"%PY_EXE%" -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
pause
