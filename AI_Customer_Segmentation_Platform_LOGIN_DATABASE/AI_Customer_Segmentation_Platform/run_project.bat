@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher ^(py^) was not found. Install Python 3.10+ and enable Add Python to PATH.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo Creating project virtual environment...
  py -m venv .venv
  if errorlevel 1 goto fail
)
echo Installing/checking required packages...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto fail
echo Starting AI Customer Segmentation Platform...
".venv\Scripts\python.exe" backend\app.py
pause
exit /b 0
:fail
echo Setup failed. Check the error above and make sure Python and internet access are available for first-time package installation.
pause
exit /b 1
