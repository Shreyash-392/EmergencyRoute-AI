@echo off
title EmergencyRoute AI - Production Preview
cd /d "%~dp0frontend"
echo Running production preview from dist/ ...
call npm run preview
pause

