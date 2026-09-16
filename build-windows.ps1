$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root 'backend'
$desktop = Join-Path $root 'desktop'
$python = Join-Path $backend '.venv\Scripts\python.exe'

if (-not (Test-Path $python)) { python -m venv (Join-Path $backend '.venv'); $python = Join-Path $backend '.venv\Scripts\python.exe' }
& $python -m pip install -r (Join-Path $backend 'requirements.txt') pyinstaller
& $python -m PyInstaller --noconfirm --clean --onedir --name jarvis-backend --paths $backend --add-data "$root\dashboard;dashboard" --add-data "$backend\config;config" $backend\desktop_server.py
Push-Location $desktop
npm install
npm run dist
Pop-Location
Write-Host "Instalador criado em $desktop\release" -ForegroundColor Green
