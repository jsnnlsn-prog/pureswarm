# PureSwarm + OpenClaw Test Cluster Setup
# Run this in PowerShell as Administrator
# ========================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PureSwarm Test Cluster Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check what we have
Write-Host "[1/6] Checking existing tools..." -ForegroundColor Yellow

$tools = @{
    "Python" = { python --version 2>$null }
    "Node.js" = { node --version 2>$null }
    "Git" = { git --version 2>$null }
    "Docker" = { docker --version 2>$null }
    "npm" = { npm --version 2>$null }
}

$missing = @()

foreach ($tool in $tools.Keys) {
    try {
        $version = & $tools[$tool] 2>$null
        if ($version) {
            Write-Host "  [OK] $tool : $version" -ForegroundColor Green
        } else {
            Write-Host "  [MISSING] $tool" -ForegroundColor Red
            $missing += $tool
        }
    } catch {
        Write-Host "  [MISSING] $tool" -ForegroundColor Red
        $missing += $tool
    }
}

Write-Host ""

# Install missing tools via winget if available
if ($missing.Count -gt 0) {
    Write-Host "[2/6] Installing missing tools..." -ForegroundColor Yellow

    $wingetAvailable = Get-Command winget -ErrorAction SilentlyContinue

    if ($wingetAvailable) {
        foreach ($tool in $missing) {
            switch ($tool) {
                "Docker" {
                    Write-Host "  Installing Docker Desktop..." -ForegroundColor Cyan
                    winget install Docker.DockerDesktop --accept-package-agreements --accept-source-agreements
                }
                "Node.js" {
                    Write-Host "  Installing Node.js 22..." -ForegroundColor Cyan
                    winget install OpenJS.NodeJS.LTS --accept-package-agreements --accept-source-agreements
                }
                "Python" {
                    Write-Host "  Installing Python 3.12..." -ForegroundColor Cyan
                    winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
                }
                "Git" {
                    Write-Host "  Installing Git..." -ForegroundColor Cyan
                    winget install Git.Git --accept-package-agreements --accept-source-agreements
                }
            }
        }
        Write-Host ""
        Write-Host "  [!] You may need to restart your terminal after installs" -ForegroundColor Yellow
    } else {
        Write-Host "  winget not available. Manual install required:" -ForegroundColor Red
        Write-Host ""
        if ($missing -contains "Docker") {
            Write-Host "  Docker: https://www.docker.com/products/docker-desktop/" -ForegroundColor White
        }
        if ($missing -contains "Node.js") {
            Write-Host "  Node.js: https://nodejs.org/ (LTS version)" -ForegroundColor White
        }
        if ($missing -contains "Python") {
            Write-Host "  Python: https://www.python.org/downloads/" -ForegroundColor White
        }
        if ($missing -contains "Git") {
            Write-Host "  Git: https://git-scm.com/download/win" -ForegroundColor White
        }
        Write-Host ""
        Write-Host "  Install these, then re-run this script." -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "[2/6] All tools present, skipping installs" -ForegroundColor Green
}

Write-Host ""

# Check Docker is running
Write-Host "[3/6] Checking Docker daemon..." -ForegroundColor Yellow
$dockerRunning = docker info 2>$null
if ($dockerRunning) {
    Write-Host "  [OK] Docker daemon is running" -ForegroundColor Green
} else {
    Write-Host "  [!] Docker Desktop not running. Please start it and re-run." -ForegroundColor Red
    Write-Host "      Look for Docker in your system tray or Start menu." -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Start the cluster
Write-Host "[4/6] Starting Redis cluster..." -ForegroundColor Yellow
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $scriptDir

docker compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Cluster started" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Cluster failed to start" -ForegroundColor Red
    Pop-Location
    exit 1
}

Write-Host ""

# Wait for containers
Write-Host "[5/6] Waiting for containers to be healthy..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

Write-Host ""

# Install Python redis package and run test
Write-Host "[6/6] Running connectivity test..." -ForegroundColor Yellow
pip install redis --quiet 2>$null
python test_connectivity.py

Pop-Location

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Install OpenClaw:  npm install -g openclaw@latest" -ForegroundColor Gray
Write-Host "  2. Run onboarding:    openclaw onboard --install-daemon" -ForegroundColor Gray
Write-Host "  3. Start gateway:     openclaw gateway --port 18789" -ForegroundColor Gray
Write-Host ""
