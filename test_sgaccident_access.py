#!/usr/bin/env python3

import requests
import json

BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
SGACCIDENT_CHAT_ID = "-1001486947378"

def test_channel_access():
    """Test if bot can access @sgaccident channel"""
    print("=== TESTING @SGACCIDENT CHANNEL ACCESS ===\n")
    
    # Test 1: Get recent updates to see if any channel posts appear
    print("1. Testing getUpdates for any channel posts...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"limit": 10, "timeout": 5}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: OK")
            print(f"   Total updates: {len(data.get('result', []))}")
            
            for update in data.get('result', []):
                if 'channel_post' in update:
                    channel_post = update['channel_post']
                    chat = channel_post.get('chat', {})
                    print(f"   Found channel post from chat ID: {chat.get('id')} ({chat.get('title', 'Unknown')})")
                    if str(chat.get('id')) == SGACCIDENT_CHAT_ID:
                        print(f"   ✅ Found post from @sgaccident channel!")
                        text = channel_post.get('text', '')[:100] + '...' if len(channel_post.get('text', '')) > 100 else channel_post.get('text', '')
                        print(f"   Text preview: {text}")
        else:
            print(f"   Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test 2: Try to get channel info
    print(f"\n2. Testing access to channel ID {SGACCIDENT_CHAT_ID}...")
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChat"
        params = {"chat_id": SGACCIDENT_CHAT_ID}
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Channel access OK")
            result = data.get('result', {})
            print(f"   Channel title: {result.get('title', 'Unknown')}")
            print(f"   Channel type: {result.get('type', 'Unknown')}")
            print(f"   Channel username: @{result.get('username', 'No username')}")
        else:
            print(f"   ❌ Error accessing channel: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test 3: Check if we're using the right channel ID
    print(f"\n3. Checking for @sgaccident in recent updates...")
    try:
        # Get more updates with offset
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        params = {"limit": 100, "timeout": 5}
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            channels_found = set()
            
            for update in data.get('result', []):
                if 'channel_post' in update:
                    channel_post = update['channel_post']
                    chat = channel_post.get('chat', {})
                    chat_id = str(chat.get('id', ''))
                    title = chat.get('title', 'Unknown')
                    username = chat.get('username', '')
                    
                    channels_found.add(f"ID: {chat_id}, Title: {title}, Username: @{username}")
            
            print(f"   Found {len(channels_found)} unique channels:")
            for channel in sorted(channels_found):
                print(f"   - {channel}")
                if 'sgaccident' in channel.lower():
                    print(f"     ⭐ This looks like the @sgaccident channel!")
        else:
            print(f"   Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")

if __name__ == "__main__":
    test_channel_access()