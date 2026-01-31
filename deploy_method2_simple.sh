#!/bin/bash
# Simple Google Cloud VM deployment for Method 2

PROJECT_ID="verdant-petal-485213-h2"
VM_NAME="accident-monitor"
ZONE="asia-southeast1-a"

echo "🚀 Deploying Method 2 to Google Cloud VM..."
echo "Project: $PROJECT_ID"
echo "VM: $VM_NAME"
echo "Zone: $ZONE"

# Check if VM exists
echo "🔍 Checking VM status..."
gcloud compute instances describe $VM_NAME --zone=$ZONE --project=$PROJECT_ID --quiet

if [ $? -eq 0 ]; then
    echo "✅ VM found - uploading files..."
    
    # Upload Method 2 files
    echo "📤 Uploading user_sgaccident_monitor.py..."
    gcloud compute scp user_sgaccident_monitor.py $VM_NAME:~/ --zone=$ZONE --project=$PROJECT_ID --quiet
    
    echo "📤 Uploading session file..."
    gcloud compute scp pukiboi_session.session $VM_NAME:~/ --zone=$ZONE --project=$PROJECT_ID --quiet
    
    echo "📤 Uploading requirements..."
    gcloud compute scp requirements.txt $VM_NAME:~/ --zone=$ZONE --project=$PROJECT_ID --quiet
    
    # SSH and setup
    echo "🔧 Setting up Method 2 on VM..."
    gcloud compute ssh $VM_NAME --zone=$ZONE --project=$PROJECT_ID --quiet --command="
        echo '🐍 Installing Python requirements...'
        pip3 install --user -r requirements.txt
        
        echo '🛑 Stopping any existing monitors...'
        pkill -f waze_accident_monitor.py || true
        pkill -f user_sgaccident_monitor.py || true
        
        echo '🚀 Starting Method 2 monitoring...'
        nohup python3 user_sgaccident_monitor.py > monitor.log 2>&1 &
        
        echo '✅ Method 2 deployment completed!'
        echo 'Process status:'
        ps aux | grep python3 | grep -v grep
    "
    
    echo "🎉 Method 2 deployment completed!"
    
else
    echo "❌ VM not found. Please create VM first."
    exit 1
fi