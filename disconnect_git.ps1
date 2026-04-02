$ErrorActionPreference = "Stop"

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -Path $here

if (Test-Path -LiteralPath ".git") {
    $ts = Get-Date -Format "yyyyMMdd_HHmmss"
    $dst = ".git_backup_" + $ts
    Rename-Item -LiteralPath ".git" -NewName $dst
    Write-Host ("OK: renamed .git -> " + $dst)
} else {
    Write-Host "No .git directory found."
}

