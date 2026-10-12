@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Necesitas instalar Python 3.11 o 3.12 desde python.org y marcar Add to PATH.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
  if errorlevel 1 (echo Error al crear entorno virtual & pause & exit /b 1)
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (echo Error instalando dependencias & pause & exit /b 1)
start "" "http://127.0.0.1:8765"
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8765
pause
