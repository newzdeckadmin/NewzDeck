@echo off
setlocal
cd /d "%~dp0"
if exist "runtime\python.exe" (
  "runtime\python.exe" server.py
  exit /b %errorlevel%
)
where py >nul 2>nul && (py -3 server.py & exit /b %errorlevel%)
where python >nul 2>nul && (python server.py & exit /b %errorlevel%)
echo No Python runtime is available. Run NewzDeck.exe once to bootstrap the private runtime.
pause
