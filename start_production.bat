@echo off
title Polymarket Analytics - Production Backend

echo ================================================
echo Polymarket Analytics - Starting Production Backend
echo ================================================
echo.

cd /d "C:\Users\DALLAS COMPUTERS\polymarket-analytics"

echo Checking dependencies...
python -c "import fastapi, aiohttp, asyncpg, streamlit, pandas" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install fastapi uvicorn aiohttp asyncpg streamlit pandas requests websockets
)

echo.
echo Starting backend server on http://localhost:8000
echo Press Ctrl+C to stop
echo.

python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

pause