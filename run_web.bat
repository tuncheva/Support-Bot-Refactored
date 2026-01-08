@echo off
setlocal

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
