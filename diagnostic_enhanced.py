#!/usr/bin/env python3
"""
Simple diagnostic script to test enhanced monitor functionality
"""
import requests
import sys
import os

# Use same credentials as enhanced monitor
BOT_TOKEN = '8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ'
CHAT_ID = '-1003683261194'

def test_telegram():
    """Test Telegram functionality"""
    try:
        message = "🧪 **DIAGNOSTIC TEST**\n\n" \
                 "✅ Enhanced Waze monitor deployed\n" \
                 "🔍 System is monitoring for accidents\n" \
                 "📱 Telegram notifications working!"
        
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
        response = requests.post(url, json={
            'chat_id': CHAT_ID,
            'text': message,
            'parse_mode': 'Markdown'
        })
        
        if response.status_code == 200:
            print("✅ Telegram test successful!")
            return True
        else:
            print(f"❌ Telegram failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Telegram error: {e}")
        return False

def check_monitor_status():
    """Check if enhanced monitor is running"""
    try:
        # Check if enhanced monitor log exists and is recent
        if os.path.exists('enhanced_monitor.log'):
            with open('enhanced_monitor.log', 'r') as f:
                lines = f.readlines()
                if lines:
                    print("📊 Recent monitor activity:")
                    for line in lines[-5:]:  # Show last 5 lines
                        print(f"   {line.strip()}")
                else:
                    print("❌ Monitor log is empty")
        else:
            print("❌ Enhanced monitor log not found")
            
    except Exception as e:
        print(f"❌ Error checking monitor: {e}")

if __name__ == '__main__':
    print("🔧 Enhanced Monitor Diagnostic Test")
    print("=" * 40)
    
    print("\n1. Testing Telegram notifications...")
    telegram_ok = test_telegram()
    
    print("\n2. Checking monitor status...")
    check_monitor_status()
    
    print("\n" + "=" * 40)
    if telegram_ok:
        print("✅ System appears to be working correctly!")
        print("📱 You should receive a test notification")
    else:
        print("❌ Issues detected - check configuration")