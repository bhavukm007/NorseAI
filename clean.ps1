[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

Write-Warning "This removes NorseAI containers and database/Redis volumes, then prunes unused Docker data."
$confirmation = Read-Host "Type CLEAN to continue"
if ($confirmation -cne "CLEAN") {
    Write-Host "Clean cancelled."
    exit 0
}

docker compose down -v
if ($LASTEXITCODE -ne 0) {
    throw "Docker Compose cleanup failed."
}
docker system prune -f
if ($LASTEXITCODE -ne 0) {
    throw "Docker system prune failed."
}
Write-Host "[OK] NorseAI Docker data cleaned" -ForegroundColor Green
