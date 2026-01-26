#!/usr/bin/env python3
import requests
import json
import time
import datetime

# Configuration
BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
CHAT_ID = "-1003683261194"

def send_test_message():
    """Send a test message to verify bot is working"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": f"🧪 <b>System Test</b>\n\n📍 Testing bot connectivity\n⏰ {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n✅ Bot is working correctly!",
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("✅ Test message sent successfully!")
            return True
        else:
            print(f"❌ Failed to send test message: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error sending test message: {e}")
        return False

if __name__ == "__main__":
    print("Starting bot connectivity test...")
    send_test_message()