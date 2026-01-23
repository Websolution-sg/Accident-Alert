# Deploy to Google Cloud

This guide shows you how to deploy the Waze Accident Monitor to Google Cloud.

## Option 1: Google Compute Engine (VM) - Recommended for 24/7 monitoring

### Step 1: Create a Google Cloud Account
1. Go to https://cloud.google.com/
2. Sign up for free (you get $300 credit for 90 days)
3. Create a new project

### Step 2: Create a VM Instance
1. Go to **Compute Engine** → **VM instances**
2. Click **Create Instance**
3. Configure:
   - **Name**: waze-monitor
   - **Region**: asia-southeast1 (Singapore)
   - **Machine type**: e2-micro (free tier eligible)
   - **Boot disk**: Ubuntu 22.04 LTS (10 GB)
   - **Firewall**: Allow HTTP traffic
4. Click **Create**

### Step 3: Connect to Your VM
1. Click **SSH** button next to your instance
2. A terminal window will open

### Step 4: Set Up the Application
Run these commands in the SSH terminal:

```bash
# Update system
sudo apt-get update
sudo apt-get install -y python3-pip git

# Clone your repository
git clone https://github.com/Websolution-sg/SOS.git
cd SOS

# Install dependencies
pip3 install -r requirements.txt

# Test the script (press Ctrl+C after a few seconds to stop)
python3 waze_accident_monitor.py
```

### Step 5: Run as a Background Service (24/7)
Create a systemd service to keep it running:

```bash
# Create service file
sudo nano /etc/systemd/system/waze-monitor.service
```

Paste this content:
```ini
[Unit]
Description=Waze Accident Monitor
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/SOS
ExecStart=/usr/bin/python3 /home/YOUR_USERNAME/SOS/waze_accident_monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Replace `YOUR_USERNAME` with your actual username (run `whoami` to check).

Save and exit (Ctrl+X, then Y, then Enter).

```bash
# Start the service
sudo systemctl daemon-reload
sudo systemctl enable waze-monitor
sudo systemctl start waze-monitor

# Check status
sudo systemctl status waze-monitor

# View logs
sudo journalctl -u waze-monitor -f
```

### Step 6: Keep It Running
Your monitor is now running 24/7! The VM will automatically restart the service if it crashes.

**Commands to manage:**
- Stop: `sudo systemctl stop waze-monitor`
- Start: `sudo systemctl start waze-monitor`
- Restart: `sudo systemctl restart waze-monitor`
- View logs: `sudo journalctl -u waze-monitor -f`

---

## Option 2: Google Cloud Run (Simpler, but may have limitations)

### Prerequisites
1. Install Google Cloud SDK: https://cloud.google.com/sdk/docs/install
2. Login: `gcloud auth login`
3. Set project: `gcloud config set project YOUR_PROJECT_ID`

### Deploy
```bash
# Build and deploy
gcloud run deploy waze-monitor \
  --source . \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --min-instances 1 \
  --max-instances 1 \
  --memory 256Mi \
  --cpu 1
```

**Note:** Cloud Run is designed for request-driven workloads. For continuous monitoring, Option 1 (VM) is better.

---

## Option 3: Using Docker Locally (Testing)

```bash
# Build Docker image
docker build -t waze-monitor .

# Run container
docker run -d --name waze-monitor --restart unless-stopped waze-monitor

# View logs
docker logs -f waze-monitor

# Stop
docker stop waze-monitor
```

---

## Costs

**Free Tier (Option 1 - VM):**
- e2-micro instance in us-central1/us-east1/us-west1
- If you choose Singapore region (asia-southeast1), there may be small charges (~$3-5/month)

**Always Free:**
- 1 non-preemptible e2-micro VM instance per month
- 30 GB-months standard persistent disk
- 1 GB network egress per month (excluding some regions)

To stay within free tier:
1. Use us-central1, us-east1, or us-west1 region
2. Use e2-micro instance type
3. Use 10GB boot disk

---

## Troubleshooting

### Update code after changes
```bash
cd /home/YOUR_USERNAME/SOS
git pull
sudo systemctl restart waze-monitor
```

### VM not responding
Check if it's running in Google Cloud Console → Compute Engine

### Service not starting
```bash
sudo journalctl -u waze-monitor -n 50 --no-pager
```

### High costs
- Make sure you're using e2-micro instance
- Stop the VM when not needed: `gcloud compute instances stop waze-monitor`
- Start it again: `gcloud compute instances start waze-monitor`
