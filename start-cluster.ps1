$dir = "D:\poke_simulator\PokemonSImulator"
Set-Location $dir
$vite = "$dir\frontend\node_modules\.bin\vite.cmd"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PokemonSimulator (VM Cluster)" -ForegroundColor Cyan
Write-Host "  API → http://192.168.209.137:8000" -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Cyan

# Kill old
Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep 1

# Frontend
Write-Host "Starting Frontend..." -ForegroundColor Yellow
$env:VITE_API_HOST = "http://192.168.209.137:8000"
Start-Process -FilePath $vite -ArgumentList "--host" -WorkingDirectory "$dir\frontend" -WindowStyle Minimized
Start-Sleep 3

Start-Process "http://localhost:5173"
Write-Host "http://localhost:5173" -ForegroundColor Green
Write-Host "Stop: .\stop.ps1" -ForegroundColor Gray
