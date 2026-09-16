@echo off
setlocal
cd /d "%~dp0backend"
python run.py
if errorlevel 1 (
  echo.
  echo O Jarvis Forge encontrou uma falha. Leia a mensagem acima e tente novamente.
  pause
)
