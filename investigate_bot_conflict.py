#!/usr/bin/env python3

import requests
import json
import time

BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"

def investigate_bot_conflict():
    """Investigate what's causing the 409 conflict"""
    print("=== INVESTIGATING BOT CONFLICT SOURCE ===\n")
    
    # Test 1: Rapid succession getUpdates to see timing
    print("1. Testing rapid getUpdates calls to identify conflict pattern...")
    for i in range(5):
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        params = {"limit": 1, "timeout": 1}
        try:
            start_time = time.time()
            response = requests.get(url, params=params, timeout=3)
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    print(f"   Test {i+1}: ✅ SUCCESS ({end_time-start_time:.2f}s)")
                else:
                    print(f"   Test {i+1}: ❌ API Error: {data}")
            else:
                print(f"   Test {i+1}: ❌ HTTP {response.status_code}: {response.text[:100]}")
        except Exception as e:
            print(f"   Test {i+1}: ❌ Exception: {e}")
        
        time.sleep(2)  # Wait between tests
    
    # Test 2: Check bot info and recent activity
    print("\n2. Checking bot information...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data['result']
                print(f"   Bot name: {bot_info.get('first_name')}")
                print(f"   Bot username: @{bot_info.get('username')}")
                print(f"   Bot ID: {bot_info.get('id')}")
            else:
                print(f"   Error getting bot info: {data}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test 3: Try to get updates with different offsets
    print("\n3. Testing different update offsets...")
    for offset in [0, 1, -1]:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        params = {"offset": offset, "limit": 1, "timeout": 1}
        try:
            response = requests.get(url, params=params, timeout=3)
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    updates_count = len(data.get('result', []))
                    print(f"   Offset {offset}: ✅ Got {updates_count} updates")
                else:
                    error_code = data.get('error_code', 'unknown')
                    description = data.get('description', 'No description')
                    print(f"   Offset {offset}: ❌ Error {error_code}: {description}")
            else:
                print(f"   Offset {offset}: ❌ HTTP {response.status_code}")
        except Exception as e:
            print(f"   Offset {offset}: ❌ Exception: {e}")
    
    # Test 4: Check webhook info in detail
    print("\n4. Detailed webhook inspection...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                webhook_info = data['result']
                print(f"   Webhook URL: '{webhook_info.get('url', '')}'")
                print(f"   Has custom certificate: {webhook_info.get('has_custom_certificate', False)}")
                print(f"   Pending updates: {webhook_info.get('pending_update_count', 0)}")
                print(f"   Last error date: {webhook_info.get('last_error_date', 'None')}")
                print(f"   Last error message: '{webhook_info.get('last_error_message', '')}'")
                print(f"   Max connections: {webhook_info.get('max_connections', 'Default')}")
                allowed_updates = webhook_info.get('allowed_updates', [])
                print(f"   Allowed updates: {', '.join(allowed_updates) if allowed_updates else 'All'}")
        else:
            print(f"   Error getting webhook info: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    print("\n=== INVESTIGATION COMPLETE ===")
    print("If 409 conflicts persist, there's likely another application/script")
    print("using this bot token from a different server or service.")

if __name__ == "__main__":
    investigate_bot_conflict()