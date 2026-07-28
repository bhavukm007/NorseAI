[CmdletBinding()]
param(
    [switch]$NonInteractive
)

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

function Get-DockerPortOwners([int]$HostPort) {
    $containerIds = @(docker ps --quiet)
    foreach ($containerId in $containerIds) {
        $details = (docker inspect $containerId | ConvertFrom-Json)[0]
        $ownsPort = $false
        foreach ($publishedPort in $details.NetworkSettings.Ports.PSObject.Properties) {
            foreach ($binding in @($publishedPort.Value)) {
                if ($binding -and $binding.HostPort -eq "$HostPort") {
                    $ownsPort = $true
                }
            }
        }
        if ($ownsPort) {
            $labels = $details.Config.Labels
            [pscustomobject]@{
                Id      = $details.Id.Substring(0, 12)
                Name    = $details.Name.TrimStart("/")
                Project = if ($labels) { $labels."com.docker.compose.project" } else { $null }
                Service = if ($labels) { $labels."com.docker.compose.service" } else { $null }
            }
        }
    }
}

function Get-WindowsPortListeners([int]$HostPort) {
    $connections = @(Get-NetTCPConnection -State Listen -LocalPort $HostPort -ErrorAction SilentlyContinue)
    foreach ($processId in @($connections | ForEach-Object { $_.OwningProcess } | Sort-Object -Unique)) {
        if (-not $processId) {
            continue
        }

        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        $processDetails = $null
        try {
            $processDetails = Get-CimInstance Win32_Process -Filter "ProcessId = $processId" -ErrorAction Stop
        }
        catch {
            # Command-line access can be unavailable for protected processes.
        }

        [pscustomobject]@{
            ProcessId   = $processId
            ProcessName = if ($process) { $process.ProcessName } else { "<unavailable>" }
            CommandLine = if ($processDetails -and $processDetails.CommandLine) {
                $processDetails.CommandLine
            }
            else {
                "<unavailable>"
            }
        }
    }
}

function Assert-PortAvailable(
    [int]$HostPort,
    [string]$ExpectedService,
    [string]$Project
) {
    $dockerOwners = @(Get-DockerPortOwners $HostPort)
    if ($dockerOwners.Count -gt 0) {
        $foreignOwners = @($dockerOwners | Where-Object {
            $_.Project -ne $Project -or $_.Service -ne $ExpectedService
        })
        if ($foreignOwners.Count -gt 0) {
            foreach ($owner in $foreignOwners) {
                $composeDetails = if ($owner.Project) {
                    " (Compose project: $($owner.Project), service: $($owner.Service))"
                }
                else {
                    ""
                }
                Write-Host "[CONFLICT] Port $HostPort is published by Docker container '$($owner.Name)' [$($owner.Id)]$composeDetails." -ForegroundColor Red
            }
            throw "Port $HostPort is already published by another Docker container."
        }

        foreach ($owner in $dockerOwners) {
            Write-Success "Port $HostPort is already published by NorseAI container '$($owner.Name)'"
        }
        return
    }

    $listeners = @(Get-WindowsPortListeners $HostPort)
    if ($listeners.Count -eq 0) {
        Write-Success "Port $HostPort is available"
        return
    }

    $unrelatedListeners = @($listeners | Where-Object { $_.ProcessName -ne "com.docker.backend" })
    if ($unrelatedListeners.Count -eq 0) {
        foreach ($listener in $listeners) {
            Write-Host "[INFO] Port $HostPort listener: PID $($listener.ProcessId), process '$($listener.ProcessName)', command line: $($listener.CommandLine)"
        }
        Write-Success "Port $HostPort is held only by Docker Desktop; continuing"
        return
    }

    foreach ($listener in $listeners) {
        Write-Host "[CONFLICT] Port $HostPort listener: PID $($listener.ProcessId), process '$($listener.ProcessName)', command line: $($listener.CommandLine)" -ForegroundColor Red
    }
    throw "Port $HostPort is already in use by an unrelated application."
}

function Test-ServiceHealthy([string]$Service) {
    $containerId = docker compose ps --quiet $Service
    if ($LASTEXITCODE -ne 0 -or -not $containerId) {
        return $false
    }

    $status = docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' $containerId
    return $LASTEXITCODE -eq 0 -and $status -eq "healthy"
}

function Test-PostgresCredentials {
    $previousErrorPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        $authenticationOutput = @(
            docker compose run --rm --no-deps backend `
                python `
                -c `
                "import os; from sqlalchemy import create_engine; create_engine(os.environ['APP_DATABASE_URL']).connect().close()" 2>&1
        )
        return [pscustomobject]@{
            Succeeded = $LASTEXITCODE -eq 0
            Output    = ($authenticationOutput -join [Environment]::NewLine)
        }
    }
    finally {
        $ErrorActionPreference = $previousErrorPreference
    }
}

function Show-PostgresCredentialMismatch(
    [string]$DatabaseUser,
    [string]$DatabaseName
) {
    Write-Host ""
    Write-Host "----------------------------------------------------" -ForegroundColor Yellow
    Write-Host "Existing PostgreSQL volume appears to have been"
    Write-Host "initialized with different credentials."
    Write-Host ""
    Write-Host "Current credentials:"
    Write-Host "User:     $DatabaseUser"
    Write-Host "Database: $DatabaseName"
    Write-Host ""
    Write-Host "Existing database rejected authentication."
    Write-Host ""
    Write-Host "Possible fixes:"
    Write-Host ""
    Write-Host "1. Keep your existing database and restore the previous password."
    Write-Host ""
    Write-Host "2. Recreate the development database (this permanently deletes"
    Write-Host "   the Compose project's PostgreSQL and Redis volume data):"
    Write-Host ""
    Write-Host "docker compose down -v" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Then run:"
    Write-Host ""
    Write-Host ".\run.ps1" -ForegroundColor Cyan
    Write-Host "----------------------------------------------------" -ForegroundColor Yellow
}

function Assert-PostgresCredentials(
    [string]$DatabaseUser,
    [string]$DatabaseName
) {
    $result = Test-PostgresCredentials
    if ($result.Succeeded) {
        Write-Success "PostgreSQL credentials accepted"
        return
    }

    if ($result.Output -notmatch "password authentication failed") {
        Write-Host $result.Output -ForegroundColor Red
        throw "PostgreSQL credential validation failed for a reason other than password authentication."
    }

    Show-PostgresCredentialMismatch $DatabaseUser $DatabaseName
    if ($NonInteractive -or [Console]::IsInputRedirected) {
        throw "PostgreSQL authentication mismatch. Interactive confirmation is required to recreate volumes; no data was changed."
    }

    $confirmation = Read-Host "Type RECREATE to delete the development volumes and rebuild, or press Enter to stop"
    if ($confirmation -cne "RECREATE") {
        throw "PostgreSQL authentication mismatch. No data was changed."
    }

    Write-Warning "Deleting this Compose project's PostgreSQL and Redis development volumes."
    docker compose down --volumes
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose could not remove the development volumes."
    }

    Write-Step "Recreating containers with the current credentials..."
    docker compose up --build --detach
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose failed to recreate NorseAI."
    }

    Wait-Service "postgres" "PostgreSQL"
    $retry = Test-PostgresCredentials
    if (-not $retry.Succeeded) {
        Write-Host $retry.Output -ForegroundColor Red
        throw "PostgreSQL still rejected the configured credentials after recreation."
    }
    Write-Success "PostgreSQL credentials accepted after recreation"
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

$LegacyDemoPassword = "replace-with-a-strong-bootstrap-password"
$ExplicitOperatorPassword = [Environment]::GetEnvironmentVariable("OPERATOR_PASSWORD")
if (
    [string]::IsNullOrWhiteSpace($ExplicitOperatorPassword) -and
    (Get-ConfigValue "APP_ENVIRONMENT" "development") -eq "development" -and
    (Get-ConfigValue "OPERATOR_PASSWORD" "") -eq $LegacyDemoPassword
) {
    $envContents = [System.IO.File]::ReadAllText((Resolve-Path ".env"))
    $envContents = [regex]::Replace(
        $envContents,
        "(?m)^OPERATOR_PASSWORD=$([regex]::Escape($LegacyDemoPassword))\s*$",
        "OPERATOR_PASSWORD=admin123"
    )
    $envContents = [regex]::Replace(
        $envContents,
        "(?m)^APP_OPERATOR_PASSWORD=$([regex]::Escape($LegacyDemoPassword))\s*$",
        "APP_OPERATOR_PASSWORD=admin123"
    )
    [System.IO.File]::WriteAllText(
        (Resolve-Path ".env"),
        $envContents,
        [System.Text.UTF8Encoding]::new($false)
    )
    Write-Success "Updated legacy demo placeholder credentials to admin / admin123"
}

$FrontendPort = [int](Get-ConfigValue "FRONTEND_PORT" "3000")
$BackendPort = [int](Get-ConfigValue "BACKEND_PORT" "8000")
$ComposeProject = Get-ConfigValue "COMPOSE_PROJECT_NAME" "norseai"
$PostgresUser = Get-ConfigValue "POSTGRES_USER" "norseai"
$PostgresDatabase = Get-ConfigValue "POSTGRES_DB" "norseai"
$AppEnvironment = Get-ConfigValue "APP_ENVIRONMENT" "development"
$OperatorUsername = Get-ConfigValue "OPERATOR_USERNAME" "admin"
$OperatorPassword = Get-ConfigValue "OPERATOR_PASSWORD" "admin123"
$FrontendOrigin = Get-ConfigValue "FRONTEND_ORIGIN" "http://localhost:$FrontendPort"
$PublicApiBaseUrl = Get-ConfigValue "PUBLIC_API_BASE_URL" "http://localhost:$BackendPort/api/v1"
$env:FRONTEND_ORIGIN = $FrontendOrigin
$env:PUBLIC_API_BASE_URL = $PublicApiBaseUrl

Write-Step "Checking ports..."
Assert-PortAvailable $FrontendPort "frontend" $ComposeProject
Assert-PortAvailable $BackendPort "backend" $ComposeProject

$RequiredServices = @("postgres", "redis", "opa", "backend", "frontend")
$StackIsHealthy = $true
foreach ($service in $RequiredServices) {
    if (-not (Test-ServiceHealthy $service)) {
        $StackIsHealthy = $false
        break
    }
}

if ($StackIsHealthy) {
    Write-Success "Existing NorseAI stack is healthy; reusing it"
}
else {
    Write-Step "Building and starting containers..."
    docker compose up --build --detach
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Docker Compose reported a startup failure. Checking service health for a specific diagnosis..."
    }
}

Write-Step "Waiting for services..."
Wait-Service "postgres" "PostgreSQL"
Assert-PostgresCredentials $PostgresUser $PostgresDatabase
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

if ($AppEnvironment -eq "development") {
    $backendLogs = @(docker compose logs --no-color --no-log-prefix backend 2>$null)
    $administratorCreated = -not $StackIsHealthy -and (
        $backendLogs -match "demo_administrator_created"
    )
    if ($administratorCreated) {
        Write-Host ""
        Write-Host "=====================================" -ForegroundColor DarkCyan
        Write-Host "Demo credentials" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Username: $OperatorUsername"
        Write-Host "Password: $OperatorPassword"
        Write-Host ""
        Write-Host "Change these credentials before production deployment." -ForegroundColor Yellow
        Write-Host "=====================================" -ForegroundColor DarkCyan
    }
    else {
        Write-Host ""
        Write-Host "Demo administrator detected." -ForegroundColor Green
    }
}
