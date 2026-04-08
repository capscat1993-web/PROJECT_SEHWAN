# Kill anything listening on port 8000, then start uvicorn (project root).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

$port = 8000
$pids = @(
    Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
) | Where-Object { $_ -and $_ -ne 0 }

foreach ($p in $pids) {
    try {
        Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
        Write-Host "Stopped PID $p (was using port $port)"
    } catch {}
}

Start-Sleep -Seconds 1

$uvicorn = Join-Path $root ".venv\Scripts\uvicorn.exe"
if (-not (Test-Path -LiteralPath $uvicorn)) {
    Write-Host "Missing $uvicorn — activate venv and pip install uvicorn first."
    exit 1
}

Write-Host "Starting uvicorn on http://127.0.0.1:$port ..."
& $uvicorn "app.main:app" --host "0.0.0.0" --port $port --reload
