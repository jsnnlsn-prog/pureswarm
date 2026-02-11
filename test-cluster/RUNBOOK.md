# PureSwarm Test Cluster Runbook

Quick reference for when you're back with food.

---

## Option A: One-Command Setup (Recommended)

Open PowerShell **as Administrator** and run:

```powershell
cd C:\Users\Jnel9\OneDrive\Desktop\pureswarm-v0.1.0\pureswarm-v0.1.0\test-cluster
.\setup.ps1
```

This will:
1. Check what's installed
2. Install missing tools via winget
3. Start the Redis cluster
4. Run the connectivity test

---

## Option B: Manual Step-by-Step

### 1. Install Docker Desktop
```powershell
winget install Docker.DockerDesktop
```
Or download: https://www.docker.com/products/docker-desktop/

**After install: Start Docker Desktop and wait for it to be ready (whale icon in system tray)**

### 2. Install Node.js 22+
```powershell
winget install OpenJS.NodeJS.LTS
```
Or download: https://nodejs.org/

### 3. Restart your terminal (important!)

### 4. Start the cluster
```powershell
cd C:\Users\Jnel9\OneDrive\Desktop\pureswarm-v0.1.0\pureswarm-v0.1.0\test-cluster
docker compose up -d
```

### 5. Verify
```powershell
docker ps
# Should show: redis-1, redis-2, redis-3, test-runner
```

### 6. Run the test
```powershell
pip install redis
python test_connectivity.py
```

---

## After Cluster is Running: Install OpenClaw

```powershell
# Install OpenClaw globally
npm install -g openclaw@latest

# Run the onboarding wizard
openclaw onboard --install-daemon

# Start the gateway
openclaw gateway --port 18789
```

Dashboard will be at: http://127.0.0.1:18789/

---

## Quick Commands Reference

| Action | Command |
|--------|---------|
| Start cluster | `docker compose up -d` |
| Stop cluster | `docker compose down` |
| View logs | `docker compose logs -f` |
| Restart cluster | `docker compose restart` |
| Nuke everything | `docker compose down -v` |
| Redis CLI | `docker exec -it redis-1 redis-cli -a [REDACTED_REDIS_PASSWORD]` |

---

## Troubleshooting

**"docker: command not found"**
→ Docker Desktop not installed or not in PATH. Restart terminal after install.

**"Cannot connect to Docker daemon"**
→ Docker Desktop isn't running. Start it from Start menu.

**"Port already in use"**
→ Something else using 6379/6380/6381. Run: `netstat -ano | findstr :6379`

**Redis test fails**
→ Wait 10 seconds for containers to fully start, then retry.

---

## Architecture We're Building

```
You (Phone/Desktop)
       ↓
   [OpenClaw]  ← WhatsApp/Telegram/Discord
       ↓
   [PureSwarm Bridge]
       ↓
   [Redis Cluster]  ← Dynomite layer (next step)
       ↓
   [Agent Swarm]  ← Consensus protocol
```

---

Ready when you are. 🐝
