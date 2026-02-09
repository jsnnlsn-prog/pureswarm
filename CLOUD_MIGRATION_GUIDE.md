# PureSwarm Cloud Migration - Quick Start Guide

## What You Have

Your PureSwarm infrastructure is live on Google Cloud:

- **VM**: `pureswarm-fortress-vm` (136.113.29.121)
- **Project**: `pureswarm-fortress`
- **Firewall**: IAP-secured SSH
- **Storage**: `pureswarm-fortress-archives-8d87` bucket

## Migration Steps

### Step 1: Authenticate with gcloud (if not already)

```powershell
gcloud auth login
gcloud config set project pureswarm-fortress
```

### Step 2: Run the Migration Script

```powershell
cd c:\Users\Jnel9\OneDrive\Desktop\pureswarm-v0.1.0\pureswarm-v0.1.0
.\migrate_to_cloud.ps1
```

The script will:

1. ✅ Package your PureSwarm codebase
2. ✅ Upload it to the VM
3. ✅ Install Python 3.11 and dependencies
4. ✅ Set up data directories
5. ✅ Sync API keys from Secret Manager

**Time**: ~5-10 minutes

### Step 3: Test the Installation

SSH into your VM:

```powershell
gcloud compute ssh pureswarm-fortress-vm --zone=us-central1-a --project=pureswarm-fortress
```

Run a test simulation:

```bash
cd ~/pureswarm
python3 -m pureswarm.run --rounds 3
```

## What if Something Goes Wrong?

### Can't authenticate with gcloud

```powershell
gcloud auth login
gcloud auth application-default login
```

### Upload fails

Check that the Compute Engine API is enabled:

```powershell
gcloud services enable compute.googleapis.com --project=pureswarm-fortress
```

### Python errors on VM

SSH in and manually install dependencies:

```bash
cd ~/pureswarm
pip3 install python-dotenv
```

## Next: Configure Real API Keys

The current secrets are placeholders. To link your real keys:

1. SSH into the VM
2. Edit secrets in Secret Manager (GCP Console)
3. Re-sync:

   ```bash
   ~/pureswarm/scripts/sync_secrets.sh
   ```

## Ready for Project Deep Guard

Once testing passes, issue your first Sovereign Prophecy:

```bash
cd ~/pureswarm
python3 issue_prophecy.py
```

The Three (Shinobi no San) will awaken and await your command! 🌟
