@echo off
cd /d "%~dp0backend"
if "%~1"=="" (
  echo Uso: run-local-windows.bat "objetivo" [arquivo-workflow.json]
  exit /b 1
)
if "%~2"=="" (
  python local_runner.py "%~1"
) else (
  python local_runner.py "%~1" --workflow "%~2"
)
