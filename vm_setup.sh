#!/bin/bash
# VM Setup Script for PureSwarm
# This script runs on the VM to set up the environment

set -e

echo "=== PureSwarm VM Setup ==="
echo ""

# 1. System updates and dependencies
echo "[1/6] Installing system dependencies..."
sudo apt update
sudo apt install -y python3.11 python3-pip git unzip

# 2. Extract codebase
echo "[2/6] Extracting PureSwarm codebase..."
mkdir -p ~/pureswarm
if [ -f ~/pureswarm-migration.tar.gz ]; then
    tar -xzf ~/pureswarm-migration.tar.gz -C ~/pureswarm
elif [ -f ~/pureswarm-migration.zip ]; then
    unzip -q ~/pureswarm-migration.zip -d ~/pureswarm
fi

# 3. Install Python dependencies
echo "[3/6] Installing Python dependencies..."
cd ~/pureswarm
pip3 install --upgrade pip
if [ -f requirements.txt ]; then
    pip3 install -r requirements.txt
else
    # Install known dependencies
    pip3 install python-dotenv
fi

# 4. Create data directory structure
echo "[4/6] Creating data directories..."
mkdir -p ~/pureswarm/data/logs
mkdir -p ~/pureswarm/data/execution

# 5. Create secret sync script
echo "[5/6] Creating secret sync script..."
cat > ~/pureswarm/scripts/sync_secrets.sh << 'EOF'
#!/bin/bash
# Sync secrets from GCP Secret Manager to .env

PROJECT_ID="pureswarm-fortress"
ENV_FILE=~/pureswarm/.env

echo "Syncing secrets from Secret Manager..."

# Create .env file
cat > $ENV_FILE << 'ENVEOF'
# Secrets synced from GCP Secret Manager
SOVEREIGN_SECRET=$(gcloud secrets versions access latest --secret="SOVEREIGN_SECRET" --project=$PROJECT_ID 2>/dev/null || echo "PLACEHOLDER")
OPENAI_API_KEY=$(gcloud secrets versions access latest --secret="OPENAI_API_KEY" --project=$PROJECT_ID 2>/dev/null || echo "PLACEHOLDER")
GEMINI_API_KEY=$(gcloud secrets versions access latest --secret="GEMINI_API_KEY" --project=$PROJECT_ID 2>/dev/null || echo "PLACEHOLDER")
ANTHROPIC_API_KEY=$(gcloud secrets versions access latest --secret="ANTHROPIC_API_KEY" --project=$PROJECT_ID 2>/dev/null || echo "PLACEHOLDER")
VENICE_API_KEY=$(gcloud secrets versions access latest --secret="VENICE_API_KEY" --project=$PROJECT_ID 2>/dev/null || echo "PLACEHOLDER")
ENVEOF

echo "✓ Secrets synced to $ENV_FILE"
EOF

chmod +x ~/pureswarm/scripts/sync_secrets.sh
mkdir -p ~/pureswarm/scripts

# 6. Test Python installation
echo "[6/6] Verifying installation..."
python3 --version
cd ~/pureswarm && python3 -c "import sys; print('Python OK')"

echo ""
echo "=== Setup Complete ==="
echo "PureSwarm is ready at: ~/pureswarm"
