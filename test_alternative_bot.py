#!/usr/bin/env python3
import requests
import json

BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
TARGET_CHANNEL = "-1003683261194"

print("🔍 TESTING ALTERNATIVE BOT TOKEN")
print("=" * 60)
print(f"Bot Token: {BOT_TOKEN}")
print(f"Channel: {TARGET_CHANNEL}")
print(f"Channel URL: https://web.telegram.org/a/#{TARGET_CHANNEL}")
print("=" * 60)

# Step 1: Verify bot token is valid
print("Step 1: Verifying bot token...")
try:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        data = response.json()
        if data.get('ok'):
            bot_info = data.get('result', {})
            print("✅ Bot token VALID")
            print(f"   Bot name: {bot_info.get('first_name')}")
            print(f"   Bot username: @{bot_info.get('username')}")
            print(f"   Bot ID: {bot_info.get('id')}")
        else:
            print(f"❌ Bot token INVALID: {data.get('description')}")
            exit()
    else:
        print(f"❌ Bot token check failed: HTTP {response.status_code}")
        exit()
except Exception as e:
    print(f"❌ Error checking bot token: {e}")
    exit()

# Step 2: Test channel access
print()
print("Step 2: Testing channel access...")
try:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChat"
    response = requests.get(url, params={'chat_id': TARGET_CHANNEL}, timeout=10)
    
    print(f"HTTP Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('ok'):
            chat_info = data.get('result', {})
            print("✅ CHANNEL ACCESS CONFIRMED")
            print(f"   Channel title: {chat_info.get('title')}")
            print(f"   Channel type: {chat_info.get('type')}")
            print(f"   Channel username: {chat_info.get('username', 'Private channel')}")
            access_confirmed = True
        else:
            print(f"❌ CHANNEL ACCESS DENIED: {data.get('description')}")
            access_confirmed = False
    elif response.status_code == 400:
        print("❌ CHANNEL ACCESS DENIED: Bad Request (400)")
        print("   This usually means:")
        print("   • Bot is not added to the channel")
        print("   • Bot lacks admin permissions")
        print("   • Channel ID is incorrect")
        access_confirmed = False
    elif response.status_code == 403:
        print("❌ CHANNEL ACCESS DENIED: Forbidden (403)")
        print("   Bot lacks permissions to access this channel")
        access_confirmed = False
    else:
        print(f"❌ CHANNEL ACCESS FAILED: HTTP {response.status_code}")
        access_confirmed = False
        
except Exception as e:
    print(f"❌ Error testing channel access: {e}")
    access_confirmed = False

# Step 3: Test message sending capability (only if channel access works)
if access_confirmed:
    print()
    print("Step 3: Testing message sending...")
    try:
        test_message = "🔧 Alternative bot access test"
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TARGET_CHANNEL,
            'text': test_message
        }
        response = requests.post(url, json=payload, timeout=10)
        
        print(f"Send Message HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                print("✅ MESSAGE SENDING CONFIRMED")
                # Try to delete the test message
                message_id = data.get('result', {}).get('message_id')
                if message_id:
                    delete_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage"
                    delete_payload = {'chat_id': TARGET_CHANNEL, 'message_id': message_id}
                    delete_response = requests.post(delete_url, json=delete_payload, timeout=5)
                    if delete_response.status_code == 200:
                        print("   Test message deleted successfully")
                send_confirmed = True
            else:
                print(f"❌ MESSAGE SENDING FAILED: {data.get('description')}")
                send_confirmed = False
        else:
            print(f"❌ MESSAGE SENDING FAILED: HTTP {response.status_code}")
            send_confirmed = False
            
    except Exception as e:
        print(f"❌ Error testing message sending: {e}")
        send_confirmed = False
else:
    send_confirmed = False

print()
print("=" * 60)
print("CONCLUSION:")
if access_confirmed and send_confirmed:
    print("✅ ALTERNATIVE BOT TOKEN WORKS!")
    print("✅ Ready to post accidents automatically")
    print("✅ This bot has full access to your channel")
elif access_confirmed:
    print("✅ Bot can access channel but cannot send messages")
    print("❌ Bot needs 'Post Messages' permission")
else:
    print("❌ Alternative bot token CANNOT ACCESS your channel")
    print("❌ Bot needs to be added as admin to the channel")
print("=" * 60)

# Compare with previous bot
print()
print("📊 COMPARISON:")
print("Previous bot: 8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ (@Accident_try_bot) - NO ACCESS")
print(f"This bot:     {BOT_TOKEN} - {'FULL ACCESS' if (access_confirmed and send_confirmed) else 'NO ACCESS'}")