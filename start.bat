@echo off
echo.
echo ====================================
echo  Roze AI Chat - Staging Deployment
echo ====================================
echo.
echo [1] Run with Ngrok (Public URL)
echo [2] Run Locally (localhost only)
echo [3] View Documentation
echo [4] Exit
echo.
set /p choice="Select option (1-4): "

if "%choice%"=="1" (
    echo.
    echo Starting with ngrok tunnel...
    echo Your staging site will be able to connect!
    echo.
    python run_public.py
)

if "%choice%"=="2" (
    echo.
    echo Starting locally on http://localhost:8002
    echo Only accessible from this computer.
    echo.
    python -m uvicorn main:app --reload --port 8002
)

if "%choice%"=="3" (
    echo.
    echo Opening documentation...
    start STAGING_DEPLOYMENT.md
    pause
)

if "%choice%"=="4" (
    exit
)

pause
