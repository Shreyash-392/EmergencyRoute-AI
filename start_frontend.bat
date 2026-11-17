@echo off
title EmergencyRoute AI - Vite Frontend (Port 5173)
cd /d "%~dp0frontend"
echo Clearing Vite cache and starting development server...
call npm run dev -- --force
pause

