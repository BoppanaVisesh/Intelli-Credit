@echo off
echo ============================================
echo   INTELLI-CREDIT - LOCAL RUN (NO DOCKER)
echo ============================================
echo.

echo [STEP 1/4] Installing Backend Dependencies...
cd backend
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install backend dependencies
    pause
    exit /b 1
)

echo.
echo [STEP 2/4] Starting Backend Server...
start "Intelli-Credit Backend" cmd /k "python main.py"
timeout /t 3 /nobreak >nul

echo.
echo [STEP 3/4] Installing Frontend Dependencies...
cd ..\frontend
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install frontend dependencies
    pause
    exit /b 1
)

echo.
echo [STEP 4/4] Starting Frontend Server...
start "Intelli-Credit Frontend" cmd /k "npm run dev"

echo.
echo ============================================
echo   ✅ APPLICATION STARTED!
echo ============================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo ⏳ Wait 10 seconds, then open your browser:
echo    👉 http://localhost:3000
echo.
echo Press Ctrl+C in each window to stop the servers
echo ============================================
echo.

timeout /t 10 /nobreak
start http://localhost:3000

pause
