Write-Host "Waiting for Docker daemon to start..."
$docker = "C:\Program Files\Docker\Docker\resources\bin\docker.exe"

for ($i = 1; $i -le 40; $i++) {
    Start-Sleep -Seconds 3
    $null = & $docker ps 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Docker is ready!"
        exit 0
    }
    Write-Host "Attempt $i/40 - still starting..."
}

Write-Host "Timeout - Docker didn't start in time"
exit 1
