@echo off
setlocal

REM Ensure only ONE Flask server is running. Multiple servers on port 5000 break
REM session cookie continuity, which breaks the "pro" -> "yes" follow-up flow.
for /f "tokens=5" %%p in ('netstat -a -n -o ^| findstr ":5000" ^| findstr LISTENING') do (
  echo Found existing process on port 5000 (PID %%p). Stopping it...
  taskkill /F /PID %%p >nul 2>nul
)

REM Ensure we run with the project virtualenv interpreter so dependencies (Flask, etc.) are available.
echo Starting Flask web app (src\support_bot\web\app.py)

IF EXIST ".venv\Scripts\python.exe" (
  set "PYTHONPATH=%CD%\src"
  ".venv\Scripts\python.exe" -m support_bot.web.app
) ELSE (
  echo WARNING: .venv not found. Falling back to system python.
  set "PYTHONPATH=%CD%\src"
  python -m support_bot.web.app
)

pause
