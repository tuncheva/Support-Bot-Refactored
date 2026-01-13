Write-Host "Starting Flask web app (src\support_bot\web\app.py)"

# Ensure only ONE Flask server is running. Multiple servers on port 5000 break
# session continuity and can make UI changes appear inconsistent.
Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess -Unique |
  ForEach-Object {
    Write-Host "Found existing process on port 5000 (PID $_). Stopping it..."
    Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
  }

$env:PYTHONPATH = (Join-Path $PSScriptRoot "src")
python -m support_bot.web.app
