#!/bin/bash

# Enhanced Waze Accident Monitor - Google Cloud Deployment Script
# This script helps deploy the enhanced accident monitoring system to Google Cloud

echo "🚀 Enhanced Waze Accident Monitor - Google Cloud Deployment"
echo "============================================================"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud SDK is not installed."
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

echo "✅ Google Cloud SDK found"

# Check if user is logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n 1 &> /dev/null; then
    echo "🔐 Please log in to Google Cloud..."
    gcloud auth login
fi

# Get current project
PROJECT=$(gcloud config get-value project)
echo "📋 Current project: $PROJECT"

if [ -z "$PROJECT" ]; then
    echo "❌ No project set. Please set a project:"
    echo "gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo ""
echo "🔄 Deployment Options:"
echo "1. Deploy to App Engine (Serverless)"
echo "2. Deploy to Cloud Run (Container)"
echo "3. Create VM instructions"
echo ""
read -p "Choose deployment option (1-3): " choice

case $choice in
    1)
        echo "🚀 Deploying to App Engine..."
        echo ""
        echo "📦 Features included:"
        echo "   ✅ Monitors Waze API for Singapore accidents"
        echo "   ✅ Monitors @sgaccident Telegram channel"
        echo "   ✅ Extracts coordinates and creates map links"
        echo "   ✅ Prevents duplicate alerts by address"
        echo "   ✅ Auto-restarts if it crashes"
        echo ""
        
        # Deploy to App Engine
        gcloud app deploy --quiet
        
        if [ $? -eq 0 ]; then
            echo "✅ Deployment successful!"
            echo ""
            echo "📊 View your application:"
            echo "   • App Engine Console: https://console.cloud.google.com/appengine"
            echo "   • View Logs: gcloud app logs tail -s default"
            echo "   • Check Status: gcloud app versions list"
            echo ""
            echo "🎉 Your Enhanced Accident Monitor is now running on Google Cloud!"
        else
            echo "❌ Deployment failed. Check the error messages above."
        fi
        ;;
    
    2)
        echo "🚀 Deploying to Cloud Run..."
        
        # Build and deploy to Cloud Run
        SERVICE_NAME="accident-monitor"
        REGION="asia-southeast1"
        
        echo "📦 Building container..."
        gcloud builds submit --tag gcr.io/$PROJECT/$SERVICE_NAME
        
        echo "🚀 Deploying to Cloud Run..."
        gcloud run deploy $SERVICE_NAME \
            --image gcr.io/$PROJECT/$SERVICE_NAME \
            --platform managed \
            --region $REGION \
            --allow-unauthenticated \
            --set-env-vars="TELEGRAM_BOT_TOKEN=8339261439:AAG1DdDGnd_vY6QPBk9zsZFEL9obtncSXQA,TELEGRAM_CHANNEL_ID=-1003329968129" \
            --cpu=1 \
            --memory=512Mi \
            --timeout=3600 \
            --max-instances=1 \
            --min-instances=1
        
        if [ $? -eq 0 ]; then
            echo "✅ Cloud Run deployment successful!"
            echo ""
            echo "📊 Manage your service:"
            echo "   • Cloud Run Console: https://console.cloud.google.com/run"
            echo "   • View Logs: gcloud run services logs tail $SERVICE_NAME --region=$REGION"
            echo ""
            SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
            echo "🌐 Service URL: $SERVICE_URL"
        else
            echo "❌ Cloud Run deployment failed."
        fi
        ;;
    
    3)
        echo "🖥️  VM Deployment Instructions:"
        echo ""
        echo "1. Create a VM in Google Cloud Console"
        echo "2. SSH into the VM"
        echo "3. Run these commands:"
        echo ""
        echo "   sudo apt-get update"
        echo "   sudo apt-get install -y python3-pip git"
        echo "   git clone https://github.com/Websolution-sg/Accident-Alert.git"
        echo "   cd Accident-Alert"
        echo "   pip3 install -r requirements.txt"
        echo "   python3 waze_accident_monitor.py"
        echo ""
        echo "📖 See DEPLOYMENT.md for detailed VM setup instructions."
        ;;
    
    *)
        echo "❌ Invalid choice. Please select 1, 2, or 3."
        ;;
esac

echo ""
echo "📚 For more information, see:"
echo "   • DEPLOYMENT.md - Detailed deployment guide"
echo "   • README.md - Application documentation"
echo "   • GitHub: https://github.com/Websolution-sg/Accident-Alert"