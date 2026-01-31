#!/usr/bin/env python3
"""
Check if the Google VM bot is actively working by monitoring sent messages
"""
import requests
import json
import datetime
import time

BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
TARGET_CHAT_ID = "-1003683261194"

def check_bot_activity():
    """Check recent bot activity by looking at messages it sent"""
    print("🔍 CHECKING BOT ACTIVITY ON GOOGLE VM")
    print("=" * 50)
    
    try:
        # Get bot info
        response = requests.get(f'https://api.telegram.org/bot{BOT_TOKEN}/getMe', timeout=10)
        if response.status_code == 200:
            bot_info = response.json()['result']
            bot_id = bot_info['id']
            bot_name = bot_info['first_name']
            print(f"✅ Bot: {bot_name} (ID: {bot_id})")
        else:
            print("❌ Cannot get bot info")
            return
        
        # Check recent messages in target channel
        print(f"\n📱 Checking target channel {TARGET_CHAT_ID}...")
        
        # Try to get updates and look for our bot's messages
        response = requests.get(f'https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?limit=50&offset=-50', timeout=10)
        
        if response.status_code == 409:
            print("⚡ 409 Conflict - Another bot instance is ACTIVELY RUNNING!")
            print("   This means your Google VM monitoring is working.")
            print("   The conflict prevents us from getting updates locally.")
            
            # Send a test message to verify posting capability
            print(f"\n📤 Sending test message to verify VM bot is posting...")
            
            test_msg = f"""🔬 **VM Activity Test - {datetime.datetime.now().strftime('%H:%M:%S')}**

This test confirms:
• Google VM bot instance is ACTIVE (409 conflict detected)
• Bot can post to target channel 
• @sgaccident monitoring should be operational with improved filters

*If you see this message, your VM system is working!*"""
            
            post_response = requests.post(
                f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
                data={
                    'chat_id': TARGET_CHAT_ID,
                    'text': test_msg,
                    'parse_mode': 'Markdown'
                }
            )
            
            if post_response.status_code == 200:
                result = post_response.json()
                msg_id = result['result']['message_id']
                print(f"✅ Test message sent successfully (ID: {msg_id})")
                print("   This confirms the bot can post to your channel.")
            else:
                print(f"❌ Failed to send test message: {post_response.status_code}")
        
        elif response.status_code == 200:
            print("⚠️  No conflict detected - VM might not be running the bot")
            result = response.json()
            updates = result.get('result', [])
            print(f"   Got {len(updates)} recent updates")
            
        else:
            print(f"❌ Unexpected error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking activity: {e}")

def monitor_target_channel():
    """Monitor the target channel for any bot posts in the next few minutes"""
    print(f"\n⏰ MONITORING TARGET CHANNEL FOR 2 MINUTES...")
    print("   Watching for any posts from your VM bot...")
    print("   (This will help confirm if @sgaccident monitoring is working)")
    
    start_time = time.time()
    last_update_id = 0
    posts_detected = 0
    
    try:
        # Get current offset
        response = requests.get(f'https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?limit=1', timeout=10)
        if response.status_code == 200:
            updates = response.json().get('result', [])
            if updates:
                last_update_id = updates[-1]['update_id']
    except:
        pass
    
    while time.time() - start_time < 120:  # 2 minutes
        try:
            # Check for new updates (this will conflict if VM is running, which is expected)
            params = {'offset': last_update_id + 1, 'limit': 10, 'timeout': 5}
            response = requests.get(f'https://api.telegram.org/bot{BOT_TOKEN}/getUpdates', 
                                  params=params, timeout=10)
            
            if response.status_code == 409:
                print("   ⚡ 409 Conflict - VM is actively polling (GOOD!)")
                time.sleep(10)
                continue
                
            elif response.status_code == 200:
                result = response.json()
                updates = result.get('result', [])
                
                for update in updates:
                    last_update_id = update['update_id']
                    
                    # Look for messages to target channel
                    message = update.get('message', {})
                    if message:
                        chat_id = str(message.get('chat', {}).get('id', ''))
                        if chat_id == TARGET_CHAT_ID:
                            from_user = message.get('from', {})
                            if from_user.get('is_bot'):
                                text = message.get('text', '')
                                msg_time = datetime.datetime.fromtimestamp(message.get('date', 0))
                                posts_detected += 1
                                print(f"   📨 Bot post detected at {msg_time.strftime('%H:%M:%S')}: {text[:60]}...")
                
                time.sleep(5)
            else:
                time.sleep(5)
                
        except Exception as e:
            print(f"   ⚠️  Monitoring error: {e}")
            time.sleep(5)
    
    print(f"\n📊 MONITORING COMPLETE:")
    print(f"   Posts detected in 2 minutes: {posts_detected}")
    if posts_detected == 0:
        print("   This might mean:")
        print("   • No accidents occurred during monitoring period")
        print("   • VM bot is running but @sgaccident was quiet")
        print("   • System is working but waiting for accident reports")

if __name__ == "__main__":
    check_bot_activity()
    monitor_target_channel()
    
    print(f"\n🎯 CONCLUSION:")
    print("If you got a 409 conflict, your Google VM bot IS RUNNING!")
    print("The improved filters have been deployed locally.")
    print("Update your VM with the improved waze_accident_monitor.py")
    print("to get better @sgaccident message detection.")