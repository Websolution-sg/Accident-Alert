#!/usr/bin/env python3
import requests
import json
import datetime

# Configuration
BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
CHAT_ID = "-1003683261194"

def send_test_alert():
    """Send a test accident alert to verify the channel is working"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        
        # Create a test accident message in the exact same format
        message = f"📍 <b>Location:</b> Test Location - Marina Bay\n"
        message += f"⏰ <b>Reported:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Add test map links
        lat, lon = 1.2844, 103.8607  # Marina Bay coordinates
        google_maps_link = f"https://www.google.com/maps?q={lat},{lon}"
        waze_link = f"https://www.waze.com/ul?ll={lat},{lon}&navigate=yes"
        message += f"🗺️ [View on Google Maps]({google_maps_link})\n"
        message += f"🚗 [Open in Waze]({waze_link})\n\n"
        
        message += f"🔗 <b>Source:</b> System Test (Not Real Accident)"
        
        payload = {
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            message_id = result.get('result', {}).get('message_id', 'Unknown')
            print(f"✅ Test accident alert sent successfully!")
            print(f"   Message ID: {message_id}")
            print(f"   Channel: {CHAT_ID}")
            return True
        else:
            print(f"❌ Failed to send test alert: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error sending test alert: {e}")
        return False

def check_recent_messages():
    """Check recent messages in the channel"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        params = {"limit": 10, "timeout": 5}
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            updates = data.get('result', [])
            print(f"✅ Retrieved {len(updates)} recent updates from bot")
            return len(updates) > 0
        else:
            print(f"❌ Failed to get updates: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error getting updates: {e}")
        return False

if __name__ == "__main__":
    print("=== TESTING ACCIDENT ALERT POSTING ===")
    print()
    
    print("1. Testing bot connectivity...")
    bot_ok = check_recent_messages()
    
    print("\n2. Sending test accident alert...")
    alert_sent = send_test_alert()
    
    print("\n=== RESULTS ===")
    if alert_sent:
        print("✅ System can post accident alerts successfully")
        print("✅ Check your Telegram channel for the test message")
    else:
        print("❌ System cannot post accident alerts")
        print("❌ Check bot token and channel permissions")
    
    print(f"\nBot Token: {BOT_TOKEN[:20]}...")
    print(f"Channel ID: {CHAT_ID}")
    print(f"Test completed at: {datetime.datetime.now()}")