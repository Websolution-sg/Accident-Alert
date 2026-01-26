#!/usr/bin/env python3

import requests
import json

BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"

def clear_webhook():
    """Clear any webhook that might be configured"""
    print("=== CLEARING BOT CONFLICTS ===\n")
    
    # 1. Check current webhook status
    print("1. Checking current webhook status...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            webhook_url = data.get('result', {}).get('url', '')
            if webhook_url:
                print(f"   ❌ Webhook found: {webhook_url}")
            else:
                print("   ✅ No webhook configured")
        else:
            print(f"   Error checking webhook: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # 2. Delete webhook
    print("\n2. Deleting webhook (if any)...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
    try:
        response = requests.post(url)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                print("   ✅ Webhook deleted successfully")
            else:
                print(f"   ❌ Failed to delete webhook: {data}")
        else:
            print(f"   Error deleting webhook: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # 3. Get pending updates count
    print("\n3. Checking pending updates...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"limit": 1, "timeout": 1}
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                updates_count = len(data.get('result', []))
                print(f"   ✅ Found {updates_count} pending updates")
                
                # If there are updates, get the highest update_id and set offset
                if updates_count > 0:
                    # Get all updates to find the highest ID
                    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
                    params = {"limit": 100, "timeout": 1}
                    response = requests.get(url, params=params, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('ok'):
                            all_updates = data.get('result', [])
                            if all_updates:
                                highest_id = max(update.get('update_id', 0) for update in all_updates)
                                print(f"   Highest update ID: {highest_id}")
                                
                                # Clear all updates by setting offset to highest_id + 1
                                print("\n4. Clearing all pending updates...")
                                url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
                                params = {"offset": highest_id + 1, "limit": 1, "timeout": 1}
                                response = requests.get(url, params=params, timeout=5)
                                if response.status_code == 200:
                                    print("   ✅ All pending updates cleared")
                                else:
                                    print(f"   ❌ Error clearing updates: {response.text}")
            else:
                print(f"   ❌ Error: {data}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # 5. Test if getUpdates works now
    print("\n5. Testing getUpdates after cleanup...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"limit": 1, "timeout": 2}
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                print("   ✅ getUpdates is working now")
            else:
                print(f"   ❌ getUpdates still has issues: {data}")
        else:
            print(f"   ❌ getUpdates error: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

    print("\n=== CLEANUP COMPLETE ===")
    print("The bot should now be ready for single-instance use.")

if __name__ == "__main__":
    clear_webhook()