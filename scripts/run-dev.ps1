# Kill anything listening on port 8000, then start Django dev server (project root).
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

$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    Write-Host "Missing $python — activate venv and install dependencies first."
    exit 1
}

Write-Host "Starting Django on http://127.0.0.1:$port ..."
& $python "backend\manage.py" runserver "0.0.0.0:$port"
