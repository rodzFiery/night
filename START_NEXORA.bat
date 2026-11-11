@echo off
setlocal
title NEXORA - Local Development Server
cd /d "%~dp0"
echo.
echo ======================================================
echo                  NEXORA COMMAND DECK
echo ======================================================
echo.
if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Python virtual environment not found.
  echo Expected: %CD%\.venv\Scripts\python.exe
  echo.
  echo Open PowerShell here and set up the environment first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -c "import uvicorn; import app.main" >nul 2>&1
if errorlevel 1 (
  echo [ERROR] NEXORA cannot import its application.
  echo Showing diagnostic information:
  ".venv\Scripts\python.exe" -c "import uvicorn; import app.main"
  pause
  exit /b 1
)
echo Starting local server at http://127.0.0.1:8000
echo Keep this window open while playing.
echo Press CTRL+C to stop.
echo.
".venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
echo.
echo NEXORA server stopped. Review any errors above.
pause
