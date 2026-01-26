#!/usr/bin/env python3
"""
Final validation test - Send a test message to confirm everything works
"""
import requests

BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
CHANNEL_ID = "-1003683261194"

def test_send_message():
    """Send a test message to validate the configuration"""
    print("🧪 FINAL VALIDATION TEST")
    print("=" * 30)
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    test_message = """🔧 **CONFIGURATION TEST**

✅ Bot Token: 8306581686:AAFWGx...
✅ Channel ID: -1003683261194
✅ Channel URL: https://web.telegram.org/a/#-1003683261194

This is a test message to confirm the accident monitoring system is correctly configured for this channel only.

*Test completed at: $(date)*"""
    
    payload = {
        'chat_id': CHANNEL_ID,
        'text': test_message,
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ TEST MESSAGE SENT SUCCESSFULLY!")
                print(f"📱 Message ID: {result['result']['message_id']}")
                print(f"📅 Sent to: {result['result']['chat']['title']}")
                print(f"🎯 Channel ID: {result['result']['chat']['id']}")
                print("\n🎉 VALIDATION COMPLETE:")
                print("✅ Bot token is working")
                print("✅ Channel access confirmed")
                print("✅ Message sending functional")
                return True
            else:
                print(f"❌ Telegram API error: {result.get('description')}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Network error: {e}")
        return False

if __name__ == "__main__":
    if test_send_message():
        print("\n🚀 READY TO RUN: python waze_accident_monitor.py")
    else:
        print("\n⚠️  Configuration issues detected!")