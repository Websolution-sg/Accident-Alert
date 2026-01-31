#!/usr/bin/env python3
"""
Quick test for improved @sgaccident filtering and access
"""
import requests
import json
import datetime

BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
SGACCIDENT_CHAT_ID = "-1001486947378"

def test_channel_access():
    """Test different ways to access the @sgaccident channel"""
    print("🔍 TESTING @SGACCIDENT CHANNEL ACCESS")
    print("=" * 50)
    
    # Method 1: Try to get chat info
    try:
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/getChat'
        response = requests.post(url, data={'chat_id': SGACCIDENT_CHAT_ID}, timeout=10)
        if response.status_code == 200:
            chat_info = response.json()['result']
            print(f"✅ Method 1 - getChat: {chat_info.get('title', 'Unknown')}")
            print(f"   Type: {chat_info.get('type', 'unknown')}")
            print(f"   Members: {chat_info.get('member_count', 'unknown')}")
        else:
            print(f"❌ Method 1 - getChat failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Method 1 error: {e}")
    
    # Method 2: Try to get recent updates with longer timeout
    try:
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/getUpdates'
        params = {'timeout': 30, 'limit': 100, 'allowed_updates': ['channel_post', 'message']}
        print("\n🔄 Waiting 30 seconds for new messages...")
        
        response = requests.get(url, params=params, timeout=35)
        if response.status_code == 200:
            result = response.json()
            updates = result.get('result', [])
            print(f"✅ Method 2 - getUpdates: Received {len(updates)} updates")
            
            sgaccident_count = 0
            for update in updates:
                # Check channel_post
                if 'channel_post' in update:
                    post = update['channel_post']
                    chat_id = str(post.get('chat', {}).get('id', ''))
                    if chat_id == SGACCIDENT_CHAT_ID:
                        sgaccident_count += 1
                        text = post.get('text', '') or post.get('caption', '')
                        print(f"   📨 Channel post {post.get('message_id')}: {text[:60]}...")
                
                # Check regular message
                if 'message' in update:
                    msg = update['message']
                    chat_id = str(msg.get('chat', {}).get('id', ''))
                    if chat_id == SGACCIDENT_CHAT_ID:
                        sgaccident_count += 1
                        text = msg.get('text', '') or msg.get('caption', '')
                        print(f"   📱 Regular message {msg.get('message_id')}: {text[:60]}...")
            
            print(f"   @sgaccident messages found: {sgaccident_count}")
            
            if sgaccident_count == 0:
                print("   ⚠️  No @sgaccident messages in this batch")
                
        else:
            print(f"❌ Method 2 failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Method 2 error: {e}")

def test_improved_filters():
    """Test the improved filtering logic"""
    print("\n🧪 TESTING IMPROVED FILTERS")
    print("=" * 50)
    
    # Test cases that might appear in @sgaccident
    test_messages = [
        "Traffic jam on PIE towards Changi Airport",
        "Accident on AYE after Jurong East exit",
        "Slow moving traffic on CTE due to vehicle breakdown",
        "Road closure on Orchard Road for construction works",
        "Congestion on BKE towards Woodlands",
        "Traffic situation at Causeway - delays from Johor",
        "Incident involving 2 cars on ECP",
        "Lane blocked on SLE near Yishun",
        "Malaysia KL traffic update - not Singapore related",
        "Heavy traffic in KL city center"
    ]
    
    # Import the improved functions
    import sys, os
    sys.path.insert(0, os.getcwd())
    
    # Test current script logic
    from waze_accident_monitor import is_accident_related, contains_malaysia_keywords
    
    print("Testing improved accident detection:")
    for i, msg in enumerate(test_messages, 1):
        accident_related = is_accident_related(msg)
        malaysia_related = contains_malaysia_keywords(msg)
        would_process = accident_related and not malaysia_related
        
        status = "✅ PROCESS" if would_process else "❌ FILTER"
        reasons = []
        if not accident_related:
            reasons.append("not accident-related")
        if malaysia_related:
            reasons.append("Malaysia-related")
        
        reason_text = f" ({', '.join(reasons)})" if reasons else ""
        print(f"  {i:2d}. {status}: {msg}{reason_text}")

if __name__ == "__main__":
    test_improved_filters()
    print()
    test_channel_access()