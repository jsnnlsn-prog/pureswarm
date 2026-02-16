#!/usr/bin/env pwsh
# PureSwarm Cloud Migration Script
# This script packages and deploys PureSwarm to the GCP VM

param(
    [string]$ProjectId = "pureswarm-fortress",
    [string]$VMName = "pureswarm-fortress-vm",
    [string]$Zone = "us-central1-a"
)

Write-Host "=== PureSwarm Cloud Migration ===" -ForegroundColor Cyan
Write-Host ""

# 1. Package the codebase
Write-Host "[1/5] Packaging PureSwarm codebase..." -ForegroundColor Yellow
$sourceDir = "c:\Users\Jnel9\OneDrive\Desktop\pureswarm-v0.1.0\pureswarm-v0.1.0"
$packagePath = "$env:TEMP\pureswarm-migration.tar.gz"

# Create tarball (using tar if available, otherwise create zip)
if (Get-Command tar -ErrorAction SilentlyContinue) {
    tar -czf $packagePath -C $sourceDir .
    Write-Host "Created tarball: $packagePath" -ForegroundColor Green
}
else {
    # Fallback: create zip
    $packagePath = "$env:TEMP\pureswarm-migration.zip"
    Compress-Archive -Path "$sourceDir\*" -DestinationPath $packagePath -Force
    Write-Host "Created archive: $packagePath" -ForegroundColor Green
}

# 2. Upload to VM
Write-Host "[2/5] Uploading to VM ($VMName)..." -ForegroundColor Yellow
gcloud compute scp $packagePath ${VMName}:~/pureswarm-migration.tar.gz --zone=$Zone --project=$ProjectId --tunnel-through-iap
if ($LASTEXITCODE -eq 0) {
    Write-Host "Upload complete" -ForegroundColor Green
}
else {
    Write-Host "Upload failed. Please ensure gcloud is authenticated." -ForegroundColor Red
    exit 1
}

# 3. Upload setup script
Write-Host "[3/5] Uploading setup script..." -ForegroundColor Yellow
$setupScriptPath = Join-Path $PSScriptRoot "vm_setup.sh"
gcloud compute scp $setupScriptPath ${VMName}:~/vm_setup.sh --zone=$Zone --project=$ProjectId --tunnel-through-iap

# 4. Execute setup on VM
Write-Host "[4/5] Installing dependencies on VM..." -ForegroundColor Yellow
$setupCommand = 'chmod +x ~/vm_setup.sh; ~/vm_setup.sh'
gcloud compute ssh $VMName --zone=$Zone --project=$ProjectId --tunnel-through-iap --command=$setupCommand

# 5. Sync secrets
Write-Host "[5/5] Syncing secrets from Secret Manager..." -ForegroundColor Yellow
$syncCommand = '~/pureswarm/scripts/sync_secrets.sh'
gcloud compute ssh $VMName --zone=$Zone --project=$ProjectId --tunnel-through-iap --command=$syncCommand

Write-Host ""
Write-Host "=== Migration Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Your PureSwarm is now running on the cloud at:" -ForegroundColor Cyan
Write-Host "  External IP: 34.57.15.201" -ForegroundColor White
Write-Host ""
Write-Host "To access the VM:" -ForegroundColor Cyan
$accessCommand = "gcloud compute ssh $VMName --zone=$Zone --project=$ProjectId --tunnel-through-iap"
Write-Host "  $accessCommand" -ForegroundColor White
Write-Host ""
Write-Host "To run a simulation:" -ForegroundColor Cyan
Write-Host "  cd ~/pureswarm" -ForegroundColor White
Write-Host "  python3 -m pureswarm.run --rounds 5" -ForegroundColor White
Write-Host ""
