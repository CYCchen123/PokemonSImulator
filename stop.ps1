Get-Job -Name "PokeAPI", "PokeWeb" -ErrorAction SilentlyContinue | Stop-Job -PassThru | Remove-Job -Force
foreach ($port in @(8000, 5173)) {
    $conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conn) {
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}
Write-Host "Stopped."
