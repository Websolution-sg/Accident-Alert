#!/usr/bin/env python3
"""
Quick test to check if Telegram API 409 conflict is resolved
"""
import requests

BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"

def test_telegram_connection():
    """Test basic Telegram API connection"""
    print("🔍 Testing Telegram API connection...")
    
    # Test getMe (should always work)
    me_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    try:
        response = requests.get(me_url, timeout=10)
        if response.status_code == 200:
            print("✅ Bot authentication: SUCCESS")
        else:
            print(f"❌ Bot authentication failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False
    
    # Test getUpdates (this was causing 409)
    updates_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {'timeout': 1, 'limit': 1}  # Very short timeout for test
    
    try:
        response = requests.get(updates_url, params=params, timeout=5)
        if response.status_code == 200:
            print("✅ GetUpdates: SUCCESS - No 409 conflict!")
            return True
        elif response.status_code == 409:
            print("❌ GetUpdates: Still getting 409 conflict")
            print("   This means another instance is still polling")
            return False
        else:
            print(f"❌ GetUpdates failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ GetUpdates error: {e}")
        return False

if __name__ == "__main__":
    if test_telegram_connection():
        print("\n🎉 All tests passed! You can now run your monitoring script.")
    else:
        print("\n⚠️ There are still issues. Check for other running instances.")
    """Test if bot can send message to the target channel"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        
        # Test message
        test_message = f"🔧 <b>System Test</b>\n\n"
        test_message += f"📍 <b>Location:</b> Test Location, Singapore\n"
        test_message += f"⏰ <b>Reported:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        test_message += f"🗺️ [View on Google Maps](https://www.google.com/maps?q=1.3521,103.8198)\n"
        test_message += f"🚗 [Open in Waze](https://www.waze.com/ul?ll=1.3521,103.8198&navigate=yes)\n\n"
        test_message += f"🔗 <b>Source:</b> System Test"
        
        payload = {
            "chat_id": CHAT_ID,
            "text": test_message,
            "parse_mode": "HTML"
        }
        
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print(f"✅ Test message sent successfully!")
                print(f"Message ID: {result['result']['message_id']}")
                print(f"Channel: {result['result']['chat']['title']}")
                return True
            else:
                print(f"❌ Telegram API error: {result.get('description')}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending test message: {e}")
        return False

def test_bot_permissions():
    """Test bot permissions and get bot info"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                bot_info = result['result']
                print(f"🤖 Bot Info:")
                print(f"   Name: {bot_info['first_name']}")
                print(f"   Username: @{bot_info['username']}")
                print(f"   ID: {bot_info['id']}")
                return True
            else:
                print(f"❌ Bot API error: {result.get('description')}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting bot info: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Telegram Bot Connection...")
    print(f"Target Channel: {CHAT_ID}")
    print("=" * 50)
    
    # Test bot permissions
    if test_bot_permissions():
        print("=" * 50)
        # Test sending message
        test_telegram_bot()
    
    print("=" * 50)
    print("Test completed!")