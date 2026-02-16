# PureSwarm Cloud Migration - Quick Start Guide

## What You Have

Your PureSwarm infrastructure is live on Google Cloud:

- **VM**: `pureswarm-node` (34.135.184.59)
- **Project**: `pureswarm-fortress`
- **Zone**: `us-central1-a`
- **Firewall**: IAP-secured SSH
- **Storage**: `pureswarm-upload-staging` bucket (temporary uploads)

## Current Status (Feb 9, 2026)

Code deployed to VM with:
- Python 3.11 + venv at `~/pureswarm/venv`
- All dependencies installed (pydantic, playwright, cryptography, etc.)
- Playwright Chromium browser installed
- `allow_external_apis = true` in config

## Quick Commands

### SSH into VM
```powershell
gcloud compute ssh pureswarm-node --zone=us-central1-a --project=pureswarm-fortress
```

### Run simulation (from VM)
```bash
cd ~/pureswarm
source venv/bin/activate
python3 run_simulation.py
```

### Issue Prophecy B (Commission Shinobi)
```bash
cd ~/pureswarm
source venv/bin/activate
python3 issue_prophecy_b.py
python3 run_simulation.py
```

### Emergency Controls
```bash
cd ~/pureswarm
source venv/bin/activate
python3 emergency.py status     # Check vault
python3 emergency.py lockout    # Kill all access
python3 emergency.py export     # Dump credentials
```

### Check Operations Log
```bash
tail -f ~/pureswarm/data/logs/shinobi_operations.log
```

## Re-deploy Code (from Windows)

If you make local changes and need to push to VM:

```powershell
# 1. Create zip (run in pureswarm directory)
powershell -Command "Get-ChildItem -Exclude 'nul','.git','__pycache__','data/browser' | Compress-Archive -DestinationPath $env:TEMP/pureswarm-migration.zip -Force"

# 2. Upload to GCS
gsutil cp "$env:TEMP/pureswarm-migration.zip" gs://pureswarm-upload-staging/

# 3. Deploy to VM
gcloud compute ssh pureswarm-node --zone=us-central1-a --command="gsutil cp gs://pureswarm-upload-staging/pureswarm-migration.zip ~/ && rm -rf ~/pureswarm && unzip -o ~/pureswarm-migration.zip -d ~/pureswarm"
```

## Troubleshooting

### Can't SSH
```powershell
gcloud compute ssh pureswarm-node --zone=us-central1-a --troubleshoot
```

### Python errors
```bash
cd ~/pureswarm
source venv/bin/activate
pip install -r requirements.txt
```

### Playwright issues
```bash
source ~/pureswarm/venv/bin/activate
playwright install chromium --with-deps
```

---

**IMPORTANT**: Always run from the VM, never from your local machine. The VM is your sandbox.
