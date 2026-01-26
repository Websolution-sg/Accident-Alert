#!/usr/bin/env python3
import requests
import json

BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
TARGET_CHAT_ID = "-1003683261194"

print("🔍 Testing your channel access...")

# Test 1: Get channel info
try:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChat"
    response = requests.get(url, params={'chat_id': TARGET_CHAT_ID}, timeout=10)
    if response.status_code == 200:
        data = response.json()
        if data.get('ok'):
            chat_info = data.get('result', {})
            print("✅ Channel access OK")
            print(f"   Channel: {chat_info.get('title', 'Unknown')}")
            print(f"   Type: {chat_info.get('type', 'Unknown')}")
        else:
            print(f"❌ Channel access failed: {data.get('description')}")
    else:
        print(f"❌ HTTP error: {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Send test message
print()
print("🔍 Testing message sending...")
try:
    test_msg = "🔧 Bot test - confirming access"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': TARGET_CHAT_ID, 'text': test_msg}
    response = requests.post(url, json=payload, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('ok'):
            print("✅ Message sending works!")
            
            # Delete the test message
            message_id = data.get('result', {}).get('message_id')
            if message_id:
                delete_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage"
                delete_payload = {'chat_id': TARGET_CHAT_ID, 'message_id': message_id}
                delete_resp = requests.post(delete_url, json=delete_payload, timeout=5)
                if delete_resp.status_code == 200:
                    print("🧹 Test message deleted")
        else:
            print(f"❌ Cannot send messages: {data.get('description')}")
    else:
        print(f"❌ HTTP error: {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*50)