#!/usr/bin/env python3
"""
Diagnostic script to check why @sgaccident messages might be filtered
"""
import requests
import json
import datetime
import re

# Configuration
BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
SGACCIDENT_CHAT_ID = "-1001486947378"

# Current filters from the main script
def is_accident_related(text):
    """Current accident keyword filter"""
    if not text:
        return False
    
    text_lower = text.lower()
    accident_keywords = [
        'accident', 'crash', 'collision', 'hit', 'injured', 'ambulance', 
        'police', 'traffic police', 'scdf', 'emergency', 'road block',
        'breakdown', 'stalled', 'blocked', 'lane closed', 'diversions'
    ]
    
    return any(keyword in text_lower for keyword in accident_keywords)

def contains_malaysia_keywords(text):
    """Current Malaysia filter"""
    if not text:
        return False
    text_lower = text.lower()
    malaysia_keywords = ['malaysia', 'johor', 'kl', 'kuala lumpur', 'selangor', 'penang', 'perak', 'kedah', 'terengganu', 'kelantan', 'pahang', 'negeri sembilan', 'melaka', 'sabah', 'sarawak']
    return any(keyword in text_lower for keyword in malaysia_keywords)

def is_accident_related_expanded(text):
    """Expanded accident keyword filter"""
    if not text:
        return False
    
    text_lower = text.lower()
    expanded_keywords = [
        # Current keywords
        'accident', 'crash', 'collision', 'hit', 'injured', 'ambulance', 
        'police', 'traffic police', 'scdf', 'emergency', 'road block',
        'breakdown', 'stalled', 'blocked', 'lane closed', 'diversions',
        
        # Additional traffic keywords
        'incident', 'situation', 'congestion', 'jam', 'slow moving', 'slow traffic',
        'vehicle', 'car trouble', 'road works', 'construction', 'closure',
        'traffic', 'disruption', 'delay', 'obstruction', 'hazard',
        'alert', 'warning', 'caution', 'avoid', 'alternative route'
    ]
    
    return any(keyword in text_lower for keyword in expanded_keywords)

def diagnose_recent_messages():
    """Analyze recent messages from @sgaccident channel"""
    print("🔍 DIAGNOSING @SGACCIDENT MESSAGE FILTERING")
    print("=" * 60)
    
    try:
        # Get recent updates
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/getUpdates'
        params = {'limit': 100, 'offset': -100}
        
        response = requests.get(url, params=params, timeout=15)
        if response.status_code != 200:
            print(f"❌ Failed to get updates: {response.status_code}")
            return
        
        result = response.json()
        updates = result.get('result', [])
        
        sgaccident_messages = []
        
        # Find @sgaccident messages
        for update in updates:
            # Check for channel posts
            if 'channel_post' in update:
                post = update['channel_post']
                chat_id = str(post.get('chat', {}).get('id', ''))
                if chat_id == SGACCIDENT_CHAT_ID:
                    sgaccident_messages.append({
                        'type': 'channel_post',
                        'message_id': post.get('message_id'),
                        'text': post.get('text', '') or post.get('caption', ''),
                        'date': post.get('date', 0)
                    })
            
            # Check for regular messages too
            if 'message' in update:
                message = update['message']
                chat_id = str(message.get('chat', {}).get('id', ''))
                if chat_id == SGACCIDENT_CHAT_ID:
                    sgaccident_messages.append({
                        'type': 'message',
                        'message_id': message.get('message_id'),
                        'text': message.get('text', '') or message.get('caption', ''),
                        'date': message.get('date', 0)
                    })
        
        if not sgaccident_messages:
            print("❌ No recent messages found from @sgaccident channel")
            print("   This could mean:")
            print("   • Bot doesn't have access to channel history")
            print("   • Channel has been quiet recently")
            print("   • Bot needs to be added to the channel")
            return
        
        print(f"✅ Found {len(sgaccident_messages)} recent @sgaccident messages")
        print("\n📋 FILTER ANALYSIS:")
        print("-" * 60)
        
        processed_count = 0
        filtered_count = 0
        
        for i, msg in enumerate(sgaccident_messages[-10:], 1):  # Check last 10
            text = msg['text']
            msg_time = datetime.datetime.fromtimestamp(msg['date']).strftime('%H:%M:%S')
            
            print(f"\n{i}. [{msg_time}] Message ID: {msg['message_id']} ({msg['type']})")
            print(f"   Text: {text[:100]}{'...' if len(text) > 100 else ''}")
            
            # Apply filters
            if not text:
                print("   ❌ FILTERED: No text content")
                filtered_count += 1
                continue
            
            if not is_accident_related(text):
                print("   ❌ FILTERED: Not accident-related (current keywords)")
                if is_accident_related_expanded(text):
                    print("   ⚠️  Would PASS with expanded keywords")
                filtered_count += 1
                continue
            
            if contains_malaysia_keywords(text):
                print("   ❌ FILTERED: Contains Malaysia keywords")
                filtered_count += 1
                continue
            
            print("   ✅ WOULD BE PROCESSED")
            processed_count += 1
        
        print("\n" + "=" * 60)
        print(f"📊 FILTERING SUMMARY:")
        print(f"   Total messages analyzed: {min(len(sgaccident_messages), 10)}")
        print(f"   Would be processed: {processed_count}")
        print(f"   Would be filtered: {filtered_count}")
        print(f"   Processing rate: {processed_count/(processed_count+filtered_count)*100:.1f}%")
        
        if filtered_count > processed_count:
            print("\n⚠️  ISSUE DETECTED: Too many messages being filtered!")
            print("   Recommendations:")
            print("   1. Expand accident keywords")
            print("   2. Review Malaysia keyword filter")
            print("   3. Check if bot has proper channel access")
        
    except Exception as e:
        print(f"❌ Error during diagnosis: {e}")

def suggest_improvements():
    """Suggest filter improvements"""
    print("\n" + "=" * 60)
    print("💡 SUGGESTED FILTER IMPROVEMENTS:")
    print("-" * 60)
    
    print("1. EXPAND ACCIDENT KEYWORDS:")
    print("   Add: 'incident', 'situation', 'congestion', 'traffic',")
    print("        'jam', 'slow moving', 'disruption', 'delay'")
    
    print("\n2. SOFTEN MALAYSIA FILTER:")
    print("   Only filter if Malaysia is the PRIMARY location")
    print("   Allow mentions of Malaysia in Singapore traffic context")
    
    print("\n3. IMPROVE MESSAGE TYPE HANDLING:")
    print("   Check both 'channel_post' and 'message' update types")
    
    print("\n4. ADD DEBUG LOGGING:")
    print("   Log filtered messages for analysis")

if __name__ == "__main__":
    diagnose_recent_messages()
    suggest_improvements()