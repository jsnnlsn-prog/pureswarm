$env:PATH = "C:\Program Files\Docker\Docker\resources\bin;" + $env:PATH
Set-Location "c:\Users\Jnel9\OneDrive\Desktop\pureswarm-v0.1.0\pureswarm-v0.1.0\test-cluster"
docker compose up -d
docker ps
