[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepositoryRoot = $PSScriptRoot
Set-Location -LiteralPath $RepositoryRoot

function Write-Step([string]$Message) {
    Write-Host ""
    Write-Host $Message -ForegroundColor Cyan
}

function Write-Success([string]$Message) {
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Get-ConfigValue([string]$Name, [string]$Default) {
    $environmentValue = [Environment]::GetEnvironmentVariable($Name)
    if (-not [string]::IsNullOrWhiteSpace($environmentValue)) {
        return $environmentValue
    }

    if (Test-Path -LiteralPath ".env") {
        $match = Get-Content -LiteralPath ".env" |
            Where-Object { $_ -match "^\s*$([regex]::Escape($Name))\s*=" } |
            Select-Object -Last 1
        if ($match) {
            return (($match -split "=", 2)[1].Trim().Trim('"').Trim("'"))
        }
    }
    return $Default
}

function Test-Port([int]$Port) {
    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $connection = $client.ConnectAsync("127.0.0.1", $Port)
        return $connection.Wait(300) -and $client.Connected
    }
    catch {
        return $false
    }
    finally {
        $client.Dispose()
    }
}

function Test-ComposeOwnsPort(
    [string]$Project,
    [string]$Service,
    [int]$ContainerPort,
    [int]$HostPort
) {
    $containerIds = @(
        docker ps --quiet `
            --filter "label=com.docker.compose.project=$Project" `
            --filter "label=com.docker.compose.service=$Service"
    )
    if ($LASTEXITCODE -ne 0 -or $containerIds.Count -eq 0) {
        return $false
    }

    foreach ($containerId in $containerIds) {
        $details = @(docker inspect $containerId | ConvertFrom-Json)
        if ($LASTEXITCODE -ne 0 -or $details.Count -eq 0) {
            continue
        }
        $binding = $details[0].NetworkSettings.Ports."$ContainerPort/tcp"
        if ($binding -and [int]$binding[0].HostPort -eq $HostPort) {
            return $true
        }
    }
    return $false
}

function Wait-Service([string]$Service, [string]$Label, [int]$TimeoutSeconds = 240) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $containerId = docker compose ps -q $Service
        if ($LASTEXITCODE -eq 0 -and $containerId) {
            $state = docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' $containerId
            if ($state -eq "healthy" -or $state -eq "running") {
                Write-Success $Label
                return
            }
            if ($state -eq "unhealthy" -or $state -eq "exited" -or $state -eq "dead") {
                docker compose logs --tail 50 $Service
                throw "$Label failed to become healthy (state: $state)."
            }
        }
        Start-Sleep -Seconds 2
    }
    docker compose logs --tail 50 $Service
    throw "Timed out waiting for $Label."
}

Write-Host "=====================================" -ForegroundColor DarkCyan
Write-Host "Starting NorseAI..." -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor DarkCyan

Write-Step "Checking Docker..."
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker is not installed or is not available on PATH."
}
docker info *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Docker Desktop is not running. Start Docker Desktop and run this command again."
}
Write-Success "Docker running"

docker compose version *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Docker Compose v2 is not available. Install or update Docker Desktop."
}
Write-Success "Docker Compose available"

if (-not (Test-Path -LiteralPath ".env")) {
    Copy-Item -LiteralPath ".env.example" -Destination ".env"
    Write-Success "Created .env from .env.example"
}

$FrontendPort = [int](Get-ConfigValue "FRONTEND_PORT" "3000")
$BackendPort = [int](Get-ConfigValue "BACKEND_PORT" "8000")
$ComposeProject = Get-ConfigValue "COMPOSE_PROJECT_NAME" "norseai"
$FrontendOrigin = Get-ConfigValue "FRONTEND_ORIGIN" "http://localhost:$FrontendPort"
$PublicApiBaseUrl = Get-ConfigValue "PUBLIC_API_BASE_URL" "http://localhost:$BackendPort/api/v1"
$env:FRONTEND_ORIGIN = $FrontendOrigin
$env:PUBLIC_API_BASE_URL = $PublicApiBaseUrl

Write-Step "Checking ports..."
if (
    (Test-Port $FrontendPort) -and
    -not (Test-ComposeOwnsPort $ComposeProject "frontend" 80 $FrontendPort)
) {
    throw "Frontend port $FrontendPort is already occupied. Set FRONTEND_PORT in .env to a free port."
}
if (
    (Test-Port $BackendPort) -and
    -not (Test-ComposeOwnsPort $ComposeProject "backend" 8000 $BackendPort)
) {
    throw "Backend port $BackendPort is already occupied. Set BACKEND_PORT in .env to a free port."
}
Write-Success "Required ports available"

Write-Step "Building and starting containers..."
docker compose up --build --detach
if ($LASTEXITCODE -ne 0) {
    throw "Docker Compose failed to start NorseAI."
}

Write-Step "Waiting for services..."
Wait-Service "postgres" "PostgreSQL"
Wait-Service "redis" "Redis"
Wait-Service "opa" "OPA"
Wait-Service "backend" "Backend"
Wait-Service "frontend" "Frontend"

$FrontendUrl = "http://localhost:$FrontendPort"
$BackendUrl = "http://localhost:$BackendPort"

Write-Host ""
Write-Host "=====================================" -ForegroundColor DarkCyan
Write-Host "NorseAI is ready!" -ForegroundColor Green
Write-Host ""
Write-Host "Frontend:"
Write-Host $FrontendUrl -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend:"
Write-Host $BackendUrl -ForegroundColor Cyan
Write-Host ""
Write-Host "Swagger:"
Write-Host "$BackendUrl/docs" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor DarkCyan
