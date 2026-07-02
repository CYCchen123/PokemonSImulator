$dir = "D:\poke_simulator\PokemonSImulator"
Set-Location $dir
$py = "$dir\venv\Scripts\python.exe"
$pip = "$dir\venv\Scripts\pip.exe"
$vite = "$dir\frontend\node_modules\.bin\vite.cmd"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PokemonSimulator" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Setup
if (-not (Test-Path $py)) {
    Write-Host "Creating venv..." -ForegroundColor Yellow
    & "$env:LocalAppData\Programs\Python\Python312\python.exe" -m venv venv
}
& $pip install fastapi uvicorn websockets -q 2>$null

if (-not (Test-Path $vite)) {
    Write-Host "npm install..." -ForegroundColor Yellow
    Set-Location $dir\frontend
    npm install --silent 2>$null
    Set-Location $dir
}

# Kill old
Write-Host "Stopping old..." -ForegroundColor Yellow
Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep 1

# Start API
Write-Host "Starting API..." -ForegroundColor Yellow
Start-Process -FilePath $py -ArgumentList "$dir\api-server\standalone_server.py" -WindowStyle Minimized
Start-Sleep 3

# Start Frontend
Write-Host "Starting Frontend..." -ForegroundColor Yellow
Start-Process -FilePath $vite -ArgumentList "--host" -WorkingDirectory "$dir\frontend" -WindowStyle Minimized
Start-Sleep 3

# Open browser
Start-Process "http://localhost:5173"
Write-Host "http://localhost:5173" -ForegroundColor Green
Write-Host "Stop: .\stop.ps1" -ForegroundColor Gray
