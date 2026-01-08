Write-Host "Starting Flask web app (src\support_bot\web\app.py)"
$env:PYTHONPATH = (Join-Path $PSScriptRoot "src")
python -m support_bot.web.app
