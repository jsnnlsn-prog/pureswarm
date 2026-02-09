# Quick Migration Fix - Manual Steps

The automated script encountered an authentication issue. Here's the quick manual process:

## Step 1: Authenticate gcloud (Required Once)

```powershell
gcloud auth login
gcloud config set project pureswarm-fortress
```

This will open a browser window for authentication.

## Step 2: Upload the Package (Already Created!)

The tarball is ready at: `C:\Users\Jnel9\AppData\Local\Temp\pureswarm-migration.tar.gz` (134 MB)

```powershell
cmd.exe /c gcloud compute scp "%TEMP%\pureswarm-migration.tar.gz" "pureswarm-fortress-vm:~/pureswarm-migration.tar.gz" --zone="us-central1-a" --project="pureswarm-fortress"
```

## Step 3: Upload Setup Script

```powershell
cmd.exe /c gcloud compute scp "c:\Users\Jnel9\OneDrive\Desktop\pureswarm-v0.1.0\pureswarm-v0.1.0\vm_setup.sh" "pureswarm-fortress-vm:~/vm_setup.sh" --zone="us-central1-a" --project="pureswarm-fortress"
```

## Step 4: Run Setup on VM

```powershell
cmd.exe /c gcloud compute ssh "pureswarm-fortress-vm" --zone="us-central1-a" --project="pureswarm-fortress" --command="chmod +x ~/vm_setup.sh; ~/vm_setup.sh"
```

## Step 5: Verify

SSH into the VM and test:

```powershell
cmd.exe /c gcloud compute ssh "pureswarm-fortress-vm" --zone="us-central1-a" --project="pureswarm-fortress"
```

Then on the VM:

```bash
cd ~/pureswarm
ls -la
python3 --version
```

**Time**: ~10 minutes after authentication
