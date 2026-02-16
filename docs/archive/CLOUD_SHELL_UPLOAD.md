# The Ronin Path - Cloud Shell Upload

**No browser automation needed. No local gcloud needed. Just pure cloud power.**

## How It Works

1. Open Google Cloud Console manually: <https://console.cloud.google.com/?project=pureswarm-fortress>
2. Click the **Cloud Shell** button (top right, terminal icon)
3. Paste these commands directly

## Step 1: Create Upload Bucket (Temporary)

```bash
# Create a staging bucket for file transfer
gsutil mb -l us-central1 gs://pureswarm-upload-staging/

# Make it private
gsutil iam ch allUsers:objectViewer gs://pureswarm-upload-staging/
gsutil iam ch -d allUsers:objectViewer gs://pureswarm-upload-staging/
```

## Step 2: Upload from Your Machine

**On your Windows machine**, run this to upload the tarball to Cloud Storage:

```powershell
# Install gsutil if needed (comes with gcloud SDK)
cmd.exe /c gsutil cp "%TEMP%\pureswarm-migration.tar.gz" gs://pureswarm-upload-staging/
```

If that fails due to auth, use the Cloud Console upload:

1. Go to: <https://console.cloud.google.com/storage/browser/pureswarm-upload-staging?project=pureswarm-fortress>
2. Click "Upload Files"
3. Select: `C:\Users\Jnel9\AppData\Local\Temp\pureswarm-migration.tar.gz`

## Step 3: Transfer to VM (Cloud Shell)

**Back in Cloud Shell**, run:

```bash
# Download from bucket to Cloud Shell
gsutil cp gs://pureswarm-upload-staging/pureswarm-migration.tar.gz ~/

# Transfer to VM
gcloud compute scp ~/pureswarm-migration.tar.gz pureswarm-fortress-vm:~/ --zone=us-central1-a

# Upload setup script too
cat > vm_setup.sh << 'SETUPEOF'
#!/bin/bash
set -e
echo "=== PureSwarm VM Setup ==="
sudo apt update && sudo apt install -y python3.11 python3-pip git
mkdir -p ~/pureswarm
tar -xzf ~/pureswarm-migration.tar.gz -C ~/pureswarm
cd ~/pureswarm
pip3 install python-dotenv
mkdir -p data/logs data/execution
echo "✓ Setup complete!"
SETUPEOF

chmod +x vm_setup.sh
gcloud compute scp vm_setup.sh pureswarm-fortress-vm:~/ --zone=us-central1-a

# Run setup
gcloud compute ssh pureswarm-fortress-vm --zone=us-central1-a --command="chmod +x ~/vm_setup.sh; ~/vm_setup.sh"
```

## Step 4: Verify

```bash
gcloud compute ssh pureswarm-fortress-vm --zone=us-central1-a --command="cd ~/pureswarm && ls -la && python3 --version"
```

## Step 5: Cleanup

```bash
gsutil rm -r gs://pureswarm-upload-staging/
```

---

**Time**: ~5 minutes  
**Browser automation needed**: Zero  
**Frank Sinatra approval rating**: 💯
