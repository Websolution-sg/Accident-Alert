#!/usr/bin/env python3
"""
Display current configuration for the cleaned up secondary channel setup
"""
import requests

# Configuration
BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
CHANNEL_ID = "-1003683261194"
CHANNEL_URL = "https://web.telegram.org/a/#-1003683261194"

def show_config():
    """Display current configuration"""
    print("🔧 CLEANED UP CONFIGURATION")
    print("=" * 40)
    print(f"📱 Channel ID: {CHANNEL_ID}")
    print(f"🌐 Channel URL: {CHANNEL_URL}")
    print(f"🤖 Bot Token: {BOT_TOKEN[:20]}...")
    
    # Get bot info
    try:
        response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe", timeout=10)
        if response.status_code == 200:
            bot_info = response.json().get('result', {})
            print(f"🎯 Bot Name: {bot_info.get('first_name', 'Unknown')}")
            print(f"📝 Bot Username: @{bot_info.get('username', 'Unknown')}")
        else:
            print("❌ Could not fetch bot information")
    except Exception as e:
        print(f"❌ Error fetching bot info: {e}")
    
    print("\n📁 FILES UPDATED:")
    print("✅ waze_accident_monitor.py - Main monitoring script")
    print("✅ app.yaml - Google Cloud deployment config") 
    print("✅ clear_webhook.py - Bot webhook management")
    print("✅ test_telegram_connection.py - Connection testing")
    
    print("\n🗃️ DATA FILES:")
    print("📄 posted_accidents_secondary.txt - Tracks posted accidents")
    print("📄 posted_addresses_secondary.txt - Tracks posted addresses")
    
    print("\n🚀 TO RUN:")
    print("python waze_accident_monitor.py")
    
    print("\n⚠️  REMOVED:")
    print("❌ Old channels - No longer referenced")
    print("❌ Old primary bot - No longer referenced")
    print("❌ Duplicate detection conflicts between channels")

if __name__ == "__main__":
    show_config()