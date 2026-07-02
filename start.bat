@echo off
cd /d "%~dp0"
echo ========================================
echo   PokemonSimulator Start
echo   %cd%
echo ========================================

:: Find Python (skip Microsoft Store stub)
set PYTHON=
if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set PYTHON=%LocalAppData%\Programs\Python\Python312\python.exe
if "%PYTHON%"=="" if exist "C:\Program Files\Python312\python.exe" set PYTHON=C:\Program Files\Python312\python.exe
if "%PYTHON%"=="" where python >nul 2>nul && set PYTHON=python
if "%PYTHON%"=="" (
    echo [ERROR] Python not found! Run: winget install Python.Python.3.12
    pause && exit /b 1
)
echo Python: %PYTHON%
%PYTHON% --version

:: Setup venv
if not exist "venv\Scripts\python.exe" (
    echo [1/4] Creating venv...
    %PYTHON% -m venv venv
    venv\Scripts\pip install fastapi uvicorn -q
)

:: Find Node
set NODE=
where node >nul 2>nul && set NODE=node
if "%NODE%"=="" (
    if exist "C:\Program Files\nodejs\node.exe" set NODE=C:\Program Files\nodejs\node.exe
)
if "%NODE%"=="" (
    echo [ERROR] Node.js not found! Install: winget install OpenJS.NodeJS.LTS
    pause && exit /b 1
)
echo Node: %NODE%

:: Setup frontend
if not exist "frontend\node_modules" (
    echo [2/4] npm install...
    cd frontend && call npm install --silent && cd ..
)

:: Dirs
mkdir data 2>nul
mkdir logs 2>nul
mkdir battle_logs\input 2>nul
mkdir battle_logs\output 2>nul

:: Kill old
echo [3/4] Stop old...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" 2^>nul') do taskkill /PID %%a /F 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173" 2^>nul') do taskkill /PID %%a /F 2>nul
timeout /t 1 /nobreak >nul

:: Start API
echo [4/4] Starting...
start "API" /B venv\Scripts\python api-server\standalone_server.py > logs\api-server.log 2>&1
cd frontend
start "Web" /B npx vite --host > ..\logs\frontend.log 2>&1
cd ..

echo.
echo ========================================
echo   http://localhost:5173
echo   http://localhost:8000
echo.
echo   Test: venv\Scripts\python scripts\gen_battle_stream.py --interval 10
echo ========================================
timeout /t 3 /nobreak >nul
start http://localhost:5173
