@echo off
chcp 65001 >nul
echo ======================================================================
echo 🚀 Progressive Planning System - Quick Start
echo ======================================================================
echo.
echo Starting API Server...
echo Please wait for "Uvicorn running on http://0.0.0.0:8000"
echo.
echo After server starts:
echo   1. Open browser: http://localhost:8000/static/progressive.html
echo   2. Enter your starting location and preferences
echo   3. Click on nodes to expand and explore
echo.
echo Press Ctrl+C to stop the server
echo ======================================================================
echo.

python api_server_progressive.py

pause
