#!/usr/bin/env python3
import requests
import json

BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
SGACCIDENT_CHAT_ID = "-1001486947378"
TARGET_CHAT_ID = "-1003683261194"

print("🔍 BOT TOKEN & CHANNEL ACCESS TEST")
print("=" * 50)

# Test 1: Bot token validity
print("1️⃣ Testing bot token validity...")
try:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        data = response.json()
        if data.get('ok'):
            bot_info = data.get('result', {})
            print("✅ Bot token VALID")
            print(f"   Bot name: {bot_info.get('first_name', 'Unknown')}")
            print(f"   Bot username: @{bot_info.get('username', 'Unknown')}")
            print(f"   Bot ID: {bot_info.get('id', 'Unknown')}")
        else:
            print(f"❌ Bot token invalid: {data.get('description')}")
    else:
        print(f"❌ HTTP error: {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# Test 2: @sgaccident channel access  
print("2️⃣ Testing @sgaccident channel access...")
try:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChat"
    response = requests.get(url, params={'chat_id': SGACCIDENT_CHAT_ID}, timeout=10)
    if response.status_code == 200:
        data = response.json()
        if data.get('ok'):
            chat_info = data.get('result', {})
            print("✅ @sgaccident channel access OK")
            print(f"   Channel: {chat_info.get('title')}")
            print(f"   Type: {chat_info.get('type')}")
            print(f"   Members: {chat_info.get('member_count', 'N/A')}")
        else:
            print(f"❌ @sgaccident failed: {data.get('description')}")
    else:
        print(f"❌ HTTP error: {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# Test 3: Target channel access
print("3️⃣ Testing target channel access...")
try:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChat"
    response = requests.get(url, params={'chat_id': TARGET_CHAT_ID}, timeout=10)
    if response.status_code == 200:
        data = response.json()
        if data.get('ok'):
            chat_info = data.get('result', {})
            print("✅ Target channel access OK")
            print(f"   Channel: {chat_info.get('title')}")
            print(f"   Type: {chat_info.get('type')}")
        else:
            print(f"❌ Target channel failed: {data.get('description')}")
    else:
        print(f"❌ HTTP error: {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# Test 4: Can send messages to target
print("4️⃣ Testing message sending capability...")
try:
    test_msg = "🔧 Bot test (will be deleted)"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': TARGET_CHAT_ID, 'text': test_msg}
    response = requests.post(url, json=payload, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('ok'):
            print("✅ Message sending OK")
            
            # Try to delete the test message
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

print()
print("=" * 50)
print("🎯 TEST COMPLETE")