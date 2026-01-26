#!/usr/bin/env python3
"""
Quick test to check if Telegram API 409 conflict is resolved - Secondary Channel
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