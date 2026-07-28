[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

Write-Host "Stopping NorseAI..." -ForegroundColor Cyan
docker compose down
if ($LASTEXITCODE -ne 0) {
    throw "Docker Compose failed to stop NorseAI."
}
Write-Host "[OK] NorseAI stopped" -ForegroundColor Green
